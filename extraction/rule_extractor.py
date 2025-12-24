"""
Rule extraction orchestrator
"""

import json
from typing import Dict, Any, List
from utils.openai_client import OpenAIClient
from ingestion.vector_store import VectorStore
from utils import prompt_templates as prompts
from models import AwardSpec
from pathlib import Path


class RuleExtractor:
    """Extract rules from award using LLM"""

    def __init__(self, openai_client: OpenAIClient, vector_store: VectorStore):
        self.openai_client = openai_client
        self.vector_store = vector_store

    def extract_award_spec(
        self,
        collection_name: str,
        award_name: str,
        award_id: str,
        source_url: str,
        award_html_path: Path,
    ) -> AwardSpec:
        """Extract complete award specification in one call using structured outputs"""

        # Query for all relevant clauses at once
        all_queries = [
            "ordinary hours span of hours weekly hours daily hours",
            "overtime time and a half double time additional hours excess hours",
            "saturday sunday weekend penalty rates",
            "public holiday rates penalties",
            "break meal rest pause penalty unpaid",
            "allowance reimbursement payment meal tool equipment",
        ]

        # Collect all relevant clauses
        # clauses_text = self._get_clauses(collection_name, all_queries)
        clauses_text = self._fake_get_clauses(award_html_path)
        print("Extracted clauses for complete award spec extraction.")
        print(clauses_text[:500])  # Print first 500 chars

        # Single LLM call with structured output
        messages = [
            {"role": "system", "content": prompts.SYSTEM_PROMPT_BASE},
            {
                "role": "user",
                "content": prompts.COMPLETE_AWARD_EXTRACTION_PROMPT.format(
                    award_name=award_name,
                    award_id=award_id,
                    source_url=source_url,
                    clauses=clauses_text,
                ),
            },
        ]

        # Use structured output with Pydantic model
        award_spec = self.openai_client.chat_completion_structured(
            messages=messages, response_format=AwardSpec
        )

        return award_spec

    def _fake_get_clauses(self, award_html_path: Path):
        html = award_html_path.read_text(encoding="utf-8")
        import markdownify as md

        markdown = md.markdownify(html)
        return markdown

    def _get_clauses(self, collection_name, all_queries):
        all_clauses = []
        seen_clause_ids = set()

        for query in all_queries:
            clauses = self.vector_store.query(collection_name, query, n_results=5)
            for clause in clauses:
                clause_id = clause["clause_id"]
                if clause_id not in seen_clause_ids:
                    all_clauses.append(clause)
                    seen_clause_ids.add(clause_id)

        clauses_text = self._format_clauses(all_clauses)
        return clauses_text

    def extract_ordinary_hours(
        self, collection_name: str, award_name: str
    ) -> Dict[str, Any]:
        """Extract ordinary hours rules"""
        # Query for relevant clauses
        clauses = self.vector_store.query(
            collection_name,
            "ordinary hours span of hours weekly hours daily hours",
            n_results=5,
        )

        clauses_text = self._format_clauses(clauses)

        # Call LLM
        messages = [
            {"role": "system", "content": prompts.SYSTEM_PROMPT_BASE},
            {
                "role": "user",
                "content": prompts.ORDINARY_HOURS_PROMPT.format(
                    award_name=award_name, clauses=clauses_text
                ),
            },
        ]

        response = self.openai_client.chat_completion(
            messages=messages, response_format={"type": "json_object"}
        )

        return json.loads(response["content"])

    def extract_overtime_rules(
        self, collection_name: str, award_name: str
    ) -> Dict[str, Any]:
        """Extract overtime rules"""
        clauses = self.vector_store.query(
            collection_name,
            "overtime time and a half double time additional hours excess hours",
            n_results=5,
        )

        clauses_text = self._format_clauses(clauses)

        messages = [
            {"role": "system", "content": prompts.SYSTEM_PROMPT_BASE},
            {
                "role": "user",
                "content": prompts.OVERTIME_RULES_PROMPT.format(
                    award_name=award_name, clauses=clauses_text
                ),
            },
        ]

        response = self.openai_client.chat_completion(
            messages=messages, response_format={"type": "json_object"}
        )

        return json.loads(response["content"])

    def extract_weekend_penalties(
        self, collection_name: str, award_name: str
    ) -> Dict[str, Any]:
        """Extract weekend penalty rates"""
        clauses = self.vector_store.query(
            collection_name, "saturday sunday weekend penalty rates", n_results=5
        )

        clauses_text = self._format_clauses(clauses)

        messages = [
            {"role": "system", "content": prompts.SYSTEM_PROMPT_BASE},
            {
                "role": "user",
                "content": prompts.WEEKEND_PENALTIES_PROMPT.format(
                    award_name=award_name, clauses=clauses_text
                ),
            },
        ]

        response = self.openai_client.chat_completion(
            messages=messages, response_format={"type": "json_object"}
        )

        return json.loads(response["content"])

    def extract_public_holiday_rules(
        self, collection_name: str, award_name: str
    ) -> Dict[str, Any]:
        """Extract public holiday rules"""
        clauses = self.vector_store.query(
            collection_name, "public holiday rates penalties", n_results=5
        )

        clauses_text = self._format_clauses(clauses)

        messages = [
            {"role": "system", "content": prompts.SYSTEM_PROMPT_BASE},
            {
                "role": "user",
                "content": prompts.PUBLIC_HOLIDAY_PROMPT.format(
                    award_name=award_name, clauses=clauses_text
                ),
            },
        ]

        response = self.openai_client.chat_completion(
            messages=messages, response_format={"type": "json_object"}
        )

        return json.loads(response["content"])

    def extract_break_rules(
        self, collection_name: str, award_name: str
    ) -> Dict[str, Any]:
        """Extract break and meal penalty rules"""
        clauses = self.vector_store.query(
            collection_name, "break meal rest pause penalty unpaid", n_results=5
        )

        clauses_text = self._format_clauses(clauses)

        messages = [
            {"role": "system", "content": prompts.SYSTEM_PROMPT_BASE},
            {
                "role": "user",
                "content": prompts.BREAK_RULES_PROMPT.format(
                    award_name=award_name, clauses=clauses_text
                ),
            },
        ]

        response = self.openai_client.chat_completion(
            messages=messages, response_format={"type": "json_object"}
        )

        return json.loads(response["content"])

    def extract_allowances(
        self, collection_name: str, award_name: str
    ) -> Dict[str, Any]:
        """Extract allowances"""
        clauses = self.vector_store.query(
            collection_name,
            "allowance reimbursement payment meal tool equipment",
            n_results=5,
        )

        clauses_text = self._format_clauses(clauses)

        messages = [
            {"role": "system", "content": prompts.SYSTEM_PROMPT_BASE},
            {
                "role": "user",
                "content": prompts.ALLOWANCES_PROMPT.format(
                    award_name=award_name, clauses=clauses_text
                ),
            },
        ]

        response = self.openai_client.chat_completion(
            messages=messages, response_format={"type": "json_object"}
        )

        return json.loads(response["content"])

    def _format_clauses(self, clauses: List[Dict[str, Any]]) -> str:
        """Format clauses for prompt"""
        formatted = []
        for clause in clauses:
            formatted.append(
                f"[{clause['clause_id']}] {clause['title']}\n{clause['text']}\n"
            )
        return "\n---\n".join(formatted)
