"""
Gap analyzer - identifies differences between award and current system
"""

import json
from typing import Dict, Any, List
from utils.openai_client import OpenAIClient
from utils import prompt_templates as prompts
from models import AwardSpec, Gap, GapReport
from datetime import datetime
import uuid


class GapAnalyzer:
    """Analyze gaps between award spec and current system"""

    def __init__(self, openai_client: OpenAIClient):
        self.openai_client = openai_client

    def analyze(
        self, award_spec: AwardSpec, current_config: Dict[str, Any], award_id: str
    ) -> GapReport:
        """
        Analyze gaps between new award and current system

        Args:
            award_spec: Extracted award specification
            current_config: Current JSON configuration
            award_id: Award ID

        Returns:
            GapReport with categorized gaps
        """
        # Prepare data for LLM
        award_spec_str = award_spec.model_dump_json(indent=2)
        current_config_str = json.dumps(current_config, indent=2)

        # Call LLM for gap analysis
        messages = [
            {"role": "system", "content": prompts.SYSTEM_PROMPT_BASE},
            {
                "role": "user",
                "content": prompts.GAP_ANALYSIS_PROMPT.format(
                    award_spec=award_spec_str, current_config=current_config_str
                ),
            },
        ]

        response = self.openai_client.chat_completion(
            messages=messages, response_format={"type": "json_object"}
        )

        gaps_data = json.loads(response["content"])

        # Convert to GapReport model
        gap_report = self._build_gap_report(gaps_data, award_id)

        return gap_report

    def _build_gap_report(self, gaps_data: Dict[str, Any], award_id: str) -> GapReport:
        """Build structured gap report from LLM response"""
        analysis_id = (
            f"gap-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        )

        report = GapReport(
            analysis_id=analysis_id,
            award_id=award_id,
            timestamp=datetime.now().isoformat(),
            gaps={"config_only": [], "code_required": [], "ambiguous": []},
        )

        # Process config-only gaps
        for idx, gap_data in enumerate(
            gaps_data.get("gaps", {}).get("config_only", [])
        ):
            gap = Gap(
                gap_id=f"{analysis_id}-config-{idx}",
                category=gap_data.get("category", "unknown"),
                severity=gap_data.get("severity", "medium"),
                gap_type="config_only",
                description=gap_data.get("description", ""),
                current_value=gap_data.get("current_value"),
                required_value=gap_data.get("required_value"),
                json_path=gap_data.get("json_path"),
                clause_reference=gap_data.get("clause_reference"),
            )
            report.gaps["config_only"].append(gap)

        # Process code-required gaps
        for idx, gap_data in enumerate(
            gaps_data.get("gaps", {}).get("code_required", [])
        ):
            gap = Gap(
                gap_id=f"{analysis_id}-code-{idx}",
                category=gap_data.get("category", "unknown"),
                severity=gap_data.get("severity", "high"),
                gap_type="code_required",
                description=gap_data.get("description", ""),
                affected_functions=gap_data.get("affected_functions", []),
                clause_reference=gap_data.get("clause_reference"),
            )
            report.gaps["code_required"].append(gap)

        # Process ambiguous gaps
        for idx, gap_data in enumerate(gaps_data.get("gaps", {}).get("ambiguous", [])):
            gap = Gap(
                gap_id=f"{analysis_id}-ambiguous-{idx}",
                category=gap_data.get("category", "unknown"),
                severity=gap_data.get("severity", "medium"),
                gap_type="ambiguous",
                description=gap_data.get("description", ""),
                clause_text=gap_data.get("clause_text"),
                clause_reference=gap_data.get("clause_reference"),
                possible_interpretations=gap_data.get("possible_interpretations", []),
                user_input_required=True,
            )
            report.gaps["ambiguous"].append(gap)

        # Build summary
        report.summary = {
            "total_gaps": (
                len(report.gaps["config_only"])
                + len(report.gaps["code_required"])
                + len(report.gaps["ambiguous"])
            ),
            "config_only": len(report.gaps["config_only"]),
            "code_required": len(report.gaps["code_required"]),
            "ambiguous": len(report.gaps["ambiguous"]),
            "estimated_dev_hours": len(report.gaps["code_required"])
            * 2.5,  # Rough estimate
        }

        return report
