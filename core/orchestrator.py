"""
Main orchestrator - coordinates the entire workflow
"""

import json
from pathlib import Path
from datetime import datetime
import uuid
from typing import Dict, Any, Optional

from utils.openai_client import OpenAIClient
from ingestion.award_fetcher import AwardFetcher
from ingestion.html_parser import HTMLParser
from ingestion.clause_chunker import ClauseChunker
from ingestion.vector_store import VectorStore
from extraction.rule_extractor import RuleExtractor
from analysis.gap_analyzer import GapAnalyzer
from generation.json_generator import ConfigGenerator
from generation.json_generator_llm import ConfigGeneratorLLM
from generation.patch_generator import PatchGenerator
from models import (
    SessionState,
    AwardSpec,
    OrdinaryHours,
    OvertimeRule,
    WeekendPenalty,
    PublicHolidayRules,
    BreakRules,
    Allowance,
)
import config


class Orchestrator:
    """Main workflow orchestrator"""

    def __init__(self, use_llm_generator: bool = False):
        """
        Initialize orchestrator

        Args:
            use_llm_generator: If True, use LLM-based config generator.
                             If False, use rule-based generator (default).
        """
        self.openai_client = OpenAIClient()
        self.vector_store = VectorStore(self.openai_client)
        self.fetcher = AwardFetcher()
        self.parser = HTMLParser()
        self.chunker = ClauseChunker()
        self.extractor = RuleExtractor(self.openai_client, self.vector_store)
        self.gap_analyzer = GapAnalyzer(self.openai_client)

        # Config generator: choose between rule-based or LLM-based
        self.use_llm_generator = use_llm_generator
        if use_llm_generator:
            self.config_generator = ConfigGeneratorLLM(self.openai_client)
        else:
            self.config_generator = ConfigGenerator()

        # Patch generator with vector store for semantic search
        self.patch_generator = PatchGenerator(self.openai_client, self.vector_store)

        self.session: Optional[SessionState] = None

    def start_session(self, award_url: str, award_id: Optional[str] = None) -> str:
        """
        Start a new analysis session

        Args:
            award_url: URL to award document
            award_id: Optional award ID (extracted from URL if not provided)

        Returns:
            Session ID
        """
        session_id = (
            f"sess-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        )

        self.session = SessionState(
            session_id=session_id,
            created_at=datetime.now(),
            status="initialized",
            input={"award_url": award_url, "award_id": award_id},
        )

        # Create session directory
        session_dir = config.SESSIONS_DIR / session_id
        session_dir.mkdir(exist_ok=True)

        self.session.artifacts["session_dir"] = str(session_dir)

        return session_id

    def fetch_and_parse(self) -> Dict[str, Any]:
        """Step 1: Fetch and parse award document"""
        self.session.status = "fetching"

        # Fetch award
        if self.session.input.get("award_id"):
            award_data = self.fetcher.fetch_from_award_id(
                self.session.input["award_id"]
            )
        else:
            award_data = self.fetcher.fetch_from_url(self.session.input["award_url"])

        # Save raw HTML
        raw_html_path = Path(self.session.artifacts["session_dir"]) / "award_raw.html"
        raw_html_path.write_text(award_data["raw_html"], encoding="utf-8")
        self.session.artifacts["raw_html_path"] = str(raw_html_path)

        # Parse HTML
        self.session.status = "parsing"
        # TODO: This parser from html to clauses is wrong - needs to be fixed
        clauses = self.parser.parse(award_data["raw_html"])

        # Chunk clauses
        chunked_clauses = self.chunker.chunk(clauses)

        # Save parsed clauses
        clauses_path = Path(self.session.artifacts["session_dir"]) / "clauses.json"
        clauses_path.write_text(json.dumps(chunked_clauses, indent=2), encoding="utf-8")
        
        return {
            "award_id": award_data["award_id"],
            "award_name": award_data["award_name"],
            "source_url": award_data["source_url"],
            "clauses_count": len(chunked_clauses),
            "clauses": chunked_clauses,
        }

    def create_vector_store(self, clauses: list) -> Dict[str, Any]:
        """Step 2: Create vector store"""
        self.session.status = "embedding"

        collection_name = f"award_{self.session.session_id}"
        self.session.vector_store_id = collection_name

        # Create collection and add clauses
        self.vector_store.create_collection(collection_name)
        result = self.vector_store.add_clauses(collection_name, clauses)

        # Track cost
        self.session.cost_breakdown["embedding"] = result["cost"]
        self.session.total_cost += result["cost"]

        return result

    def extract_rules(self, award_name: str) -> AwardSpec:
        """Step 3: Extract rules from award using single structured output call"""
        self.session.status = "extracting"

        collection_name = self.session.vector_store_id
        award_id = self.session.input.get("award_id", "unknown")
        source_url = self.session.input["award_url"]

        # Single extraction call with structured output
        award_spec = self.extractor.extract_award_spec(
            collection_name, award_name, award_id, source_url,
            Path(self.session.artifacts["session_dir"]) / "award_raw.html"
        )

        # Update metadata
        award_spec.effective_date = datetime.now().strftime("%Y-%m-%d")
        award_spec.version = "1.0"

        # Save award spec (Pydantic models have .model_dump_json() method)
        spec_path = Path(self.session.artifacts["session_dir"]) / "award_spec.json"
        spec_path.write_text(award_spec.model_dump_json(indent=2), encoding="utf-8")
        self.session.artifacts["award_spec_path"] = str(spec_path)

        # Track extraction costs
        self.session.cost_breakdown["extraction"] = (
            self.openai_client.get_session_cost() - self.session.total_cost
        )
        self.session.total_cost = self.openai_client.get_session_cost()

        return award_spec

    def analyze_gaps(self, award_spec: AwardSpec) -> Dict[str, Any]:
        """Step 4: Analyze gaps"""
        self.session.status = "analyzing_gaps"

        # Load baseline config
        baseline_path = config.DATA_DIR / "baseline_config.json"
        if baseline_path.exists():
            baseline_config = json.loads(baseline_path.read_text())
        else:
            baseline_config = {}

        # Analyze gaps
        gap_report = self.gap_analyzer.analyze(
            award_spec, baseline_config, award_spec.award_id
        )

        # Save gap report
        gap_path = Path(self.session.artifacts["session_dir"]) / "gap_report.json"
        gap_dict = {
            "analysis_id": gap_report.analysis_id,
            "award_id": gap_report.award_id,
            "timestamp": gap_report.timestamp,
            "gaps": {
                "config_only": [vars(g) for g in gap_report.gaps["config_only"]],
                "code_required": [vars(g) for g in gap_report.gaps["code_required"]],
                "ambiguous": [vars(g) for g in gap_report.gaps["ambiguous"]],
            },
            "summary": gap_report.summary,
        }
        gap_path.write_text(json.dumps(gap_dict, indent=2), encoding="utf-8")
        self.session.artifacts["gap_report_path"] = str(gap_path)

        # Track cost
        self.session.cost_breakdown["gap_analysis"] = (
            self.openai_client.get_session_cost() - self.session.total_cost
        )
        self.session.total_cost = self.openai_client.get_session_cost()

        return gap_report

    def generate_outputs(
        self, award_spec: AwardSpec, gap_report: Any
    ) -> Dict[str, str]:
        """Step 5: Generate outputs"""
        self.session.status = "generating"

        # Load baseline config
        baseline_path = config.DATA_DIR / "baseline_config.json"
        if baseline_path.exists():
            baseline_config = json.loads(baseline_path.read_text())
        else:
            baseline_config = {}

        # Generate config
        # Convert AwardSpec to dict if using rule-based generator
        if self.use_llm_generator:
            new_config = self.config_generator.generate(award_spec, baseline_config)
        else:
            # Rule-based generator expects dict
            award_spec_dict = award_spec.model_dump()
            new_config = self.config_generator.generate(
                award_spec_dict, baseline_config
            )
        config_path = (
            Path(self.session.artifacts["session_dir"]) / "updated_config.json"
        )
        config_path.write_text(json.dumps(new_config, indent=2), encoding="utf-8")
        self.session.artifacts["updated_config_path"] = str(config_path)

        # Generate patch plan with Python script path
        # Try multiple locations for the baseline Python script
        python_script_path = config.DATA_DIR / "WorkpacNonCoal+Clerks_PYscript.py"
        if not python_script_path.exists():
            # Try parent directory
            python_script_path = (
                config.DATA_DIR.parent.parent / "WorkpacNonCoal+Clerks_PYscript.py"
            )

        patch_plan = self.patch_generator.generate_patch_plan(
            gap_report, award_spec, python_script_path=str(python_script_path)
        )
        patch_path = Path(self.session.artifacts["session_dir"]) / "patch_plan.md"
        patch_path.write_text(patch_plan, encoding="utf-8")
        self.session.artifacts["patch_plan_path"] = str(patch_path)

        # Track cost
        self.session.cost_breakdown["generation"] = (
            self.openai_client.get_session_cost() - self.session.total_cost
        )
        self.session.total_cost = self.openai_client.get_session_cost()

        self.session.status = "complete"

        return {"config_path": str(config_path), "patch_plan_path": str(patch_path)}

    def get_session_cost(self) -> float:
        """Get total session cost"""
        return self.openai_client.get_session_cost()

    def get_cost_breakdown(self) -> Dict[str, float]:
        """Get detailed cost breakdown"""
        return self.session.cost_breakdown if self.session else {}
