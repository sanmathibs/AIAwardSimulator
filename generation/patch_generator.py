"""
Python patch plan generator
"""

import traceback
from typing import Dict, Any, List, Optional
from pathlib import Path
from utils.openai_client import OpenAIClient
from utils import prompt_templates as prompts
from utils.code_analyzer import PythonCodeAnalyzer
from ingestion.vector_store import VectorStore
from models import AwardSpec, GapReport
import json
import config


class PatchGenerator:
    """Generate Python patch plans for code-required gaps using function extraction and semantic search"""

    def __init__(
        self,
        openai_client: OpenAIClient,
        vector_store: Optional[VectorStore] = None,
    ):
        self.openai_client = openai_client
        self.vector_store = vector_store

    def generate_patch_plan(
        self,
        gap_report: GapReport,
        award_spec: AwardSpec,
        python_script_path: Optional[str] = None,
    ) -> str:
        """
        Generate markdown patch plan with actual code analysis

        Args:
            gap_report: Gap analysis report
            award_spec: Award specification
            python_script_path: Path to baseline Python script (optional)

        Returns:
            Markdown formatted patch plan
        """
        print("Generating Python patch plan...")

        # Only generate if there are code-required gaps
        if not gap_report.gaps["code_required"]:
            return self._generate_no_changes_plan(gap_report)

        # Load baseline Python script
        if python_script_path is None:
            python_script_path = config.DATA_DIR / "WorkpacNonCoal+Clerks_PYscript.py"
        else:
            python_script_path = Path(python_script_path)

        if not python_script_path.exists():
            print(f"Baseline Python script not found at {str(python_script_path)}")
            return self._generate_no_code_available_plan(
                gap_report, str(python_script_path)
            )

        # Read and analyze Python code
        python_code = python_script_path.read_text(encoding="utf-8")
        analyzer = PythonCodeAnalyzer(python_code)

        # Extract affected functions
        affected_function_names = self._collect_affected_functions(gap_report)
        print(f"Affected functions: {affected_function_names}")
        affected_functions = {}

        if affected_function_names:
            # Extract with dependencies (1 level deep)
            affected_functions = analyzer.extract_functions_with_dependencies(
                affected_function_names, depth=1
            )

        # Get file outline
        file_outline = analyzer.get_file_outline()

        # Get additional context via semantic search (if vector store available)
        related_context = ""
        if self.vector_store and affected_function_names:
            related_context = self._get_semantic_context(
                analyzer, gap_report, affected_function_names
            )

        # Format functions for LLM
        affected_functions_str = PythonCodeAnalyzer.format_functions_for_llm(
            affected_functions
        )
        if (
            not affected_functions_str
            or affected_functions_str == "No functions extracted."
        ):
            # Fallback: provide gap descriptions with function names
            affected_functions_str = self._format_function_references(gap_report)

        # Prepare gap report for LLM
        gap_report_dict = {
            "code_required_gaps": [
                {
                    "gap_id": gap.gap_id,
                    "category": gap.category,
                    "severity": gap.severity,
                    "description": gap.description,
                    "affected_functions": gap.affected_functions,
                    "clause_reference": gap.clause_reference,
                }
                for gap in gap_report.gaps["code_required"]
            ]
        }

        gap_report_str = json.dumps(gap_report_dict, indent=2)
        award_spec_str = award_spec.model_dump_json(indent=2)

        # Call LLM with comprehensive context
        messages = [
            {"role": "system", "content": prompts.SYSTEM_PROMPT_BASE},
            {
                "role": "user",
                "content": prompts.PATCH_PLAN_PROMPT.format(
                    gap_report=gap_report_str,
                    award_spec=award_spec_str,
                    file_outline=file_outline,
                    affected_functions=affected_functions_str,
                    related_context=related_context
                    or "No additional context available.",
                ),
            },
        ]

        print("Calling LLM for patch plan generation...")
        response = self.openai_client.chat_completion(
            messages=messages, temperature=0.3
        )

        return response["content"]

    def _collect_affected_functions(self, gap_report: GapReport) -> List[str]:
        """Collect all affected function names from gaps"""
        function_names = []
        for gap in gap_report.gaps["code_required"]:
            if gap.affected_functions:
                function_names.extend(gap.affected_functions)
        return list(set(function_names))  # Remove duplicates

    def _get_semantic_context(
        self,
        analyzer: PythonCodeAnalyzer,
        gap_report: GapReport,
        exclude_functions: List[str],
    ) -> str:
        """
        Use semantic search to find related code sections

        Args:
            analyzer: Code analyzer instance
            gap_report: Gap report with descriptions
            exclude_functions: Function names already extracted (to avoid duplication)

        Returns:
            Formatted string of related code sections
        """
        try:
            # Create collection for Python code
            collection_name = f"python_code_{gap_report.award_id}"

            # Check if collection already exists, if not create it
            try:
                self.vector_store.create_collection(collection_name)
            except:
                pass  # Collection might already exist

            # Chunk Python code by function
            chunks = analyzer.chunk_by_function()

            # Add code chunks using dedicated method
            if chunks:
                self.vector_store.add_code_chunks(collection_name, chunks)

            # Query with gap descriptions
            related_sections = []
            for gap in gap_report.gaps["code_required"]:
                query = f"{gap.description} {gap.category}"
                results = self.vector_store.query(collection_name, query, n_results=2)

                for result in results:
                    # Skip if this function is already in affected_functions
                    func_name = result.get("metadata", {}).get("name")
                    if func_name not in exclude_functions:
                        related_sections.append(result["text"])

            if related_sections:
                return "\n\n---\n\n".join(related_sections[:3])  # Top 3 results

        except Exception as e:
            traceback.print_exc()
            # Semantic search failed, return empty
            print(f"Semantic search failed: {e}")

        return ""

    def _format_function_references(self, gap_report: GapReport) -> str:
        """Format function references when extraction fails"""
        parts = ["## Function References (extraction failed, names only)\n"]
        for gap in gap_report.gaps["code_required"]:
            if gap.affected_functions:
                parts.append(f"**Gap:** {gap.description}")
                parts.append(
                    f"**Functions:** {', '.join([f'`{fn}`' for fn in gap.affected_functions])}"
                )
                parts.append("")
        return "\n".join(parts)

    def _generate_no_changes_plan(self, gap_report: GapReport) -> str:
        """Generate plan when no code changes required"""
        return f"""# Python Patch Plan: {gap_report.award_id}

## Summary

✅ **No code changes required!**

All gaps can be addressed through JSON configuration updates only.

### Gap Summary:
- **Config-Only Gaps**: {len(gap_report.gaps['config_only'])}
- **Code-Required Gaps**: {len(gap_report.gaps['code_required'])}
- **Ambiguous Items**: {len(gap_report.gaps['ambiguous'])}

### Next Steps:
1. Review and apply the updated JSON configuration
2. Test with sample shifts
3. Validate calculations match award requirements

---

**Generated**: {gap_report.timestamp}
"""

    def _generate_no_code_available_plan(
        self, gap_report: GapReport, script_path: str
    ) -> str:
        """Generate plan when Python script is not available"""
        return f"""# Python Patch Plan: {gap_report.award_id}

## ⚠️ Warning: Baseline Python Script Not Found

The baseline Python script could not be located at:
```
{script_path}
```

### Code-Required Gaps Identified: {len(gap_report.gaps['code_required'])}

{self._format_gap_list(gap_report.gaps['code_required'])}

### Recommendations:

1. **Locate the baseline Python script:**
   - Check the `data/` directory
   - Verify the file name: `WorkpacNonCoal+Clerks_PYscript.py`
   - Or provide the correct path when calling this function

2. **Manual Analysis Required:**
   - Review each gap description above
   - Identify affected functions in your codebase
   - Design implementations based on award specifications

3. **Re-run with Script Path:**
   ```python
   patch_plan = patch_generator.generate_patch_plan(
       gap_report, 
       award_spec,
       python_script_path="/path/to/your/script.py"
   )
   ```

---

**Generated**: {gap_report.timestamp}
"""

    def _format_gap_list(self, gaps: List) -> str:
        """Format list of gaps for display"""
        if not gaps:
            return "_No gaps to display_"

        parts = []
        for i, gap in enumerate(gaps, 1):
            parts.append(f"\n#### Gap #{i}: {gap.description}")
            parts.append(f"- **Category:** {gap.category}")
            parts.append(f"- **Severity:** {gap.severity}")
            if gap.affected_functions:
                parts.append(
                    f"- **Affected Functions:** {', '.join([f'`{fn}`' for fn in gap.affected_functions])}"
                )
            if gap.clause_reference:
                parts.append(f"- **Clause Reference:** {gap.clause_reference}")

        return "\n".join(parts)
