"""
Prompt templates for extraction
"""

SYSTEM_PROMPT_BASE = """You are an expert in Australian industrial relations and Fair Work awards.
Your task is to extract specific wage calculation rules from award clauses with high accuracy.

Guidelines:
- Only extract information explicitly stated in the clauses
- If information is ambiguous or missing, note it clearly
- Always include clause references for auditability
- Output valid JSON only
- Use null for missing optional fields
"""

ORDINARY_HOURS_PROMPT = """Extract ordinary hours rules from the following award clauses.

Output JSON format:
{{
  "weekly_hours": <float>,
  "span_of_hours": {{
    "weekday": {{"start": "HH:MM", "end": "HH:MM"}} or null,
    "saturday": {{"start": "HH:MM", "end": "HH:MM"}} or null,
    "sunday": {{"start": "HH:MM", "end": "HH:MM"}} or null
  }},
  "daily_threshold": <float> or null,
  "clause_references": ["Clause X.Y", ...]
}}

Award: {award_name}

Relevant clauses:
{clauses}

Extract the ordinary hours rules as JSON:"""

OVERTIME_RULES_PROMPT = """Extract overtime rules from the following award clauses.

Output JSON format:
{{
  "overtime_rules": [
    {{
      "name": "OT1",
      "trigger_type": "daily_excess" | "weekly_excess" | "after_ot1" | "outside_span",
      "factor": <float>,
      "threshold": <float> or null,
      "daily_max": <float> or null,
      "weekly_max": <float> or null,
      "applies_to": ["weekday", "saturday", "sunday"],
      "clause_references": ["Clause X.Y"]
    }}
  ]
}}

Award: {award_name}

Relevant clauses:
{clauses}

Extract the overtime rules as JSON:"""

WEEKEND_PENALTIES_PROMPT = """Extract weekend penalty rates from the following award clauses.

Output JSON format:
{{
  "weekend_penalties": [
    {{
      "name": "SAT1",
      "day": "Saturday",
      "factor": <float>,
      "time_range": {{"start": "HH:MM", "end": "HH:MM"}} or null,
      "minimum_engagement": <float> or null,
      "clause_references": ["Clause X.Y"]
    }}
  ]
}}

Award: {award_name}

Relevant clauses:
{clauses}

Extract the weekend penalty rates as JSON:"""

PUBLIC_HOLIDAY_PROMPT = """Extract public holiday rules from the following award clauses.

Output JSON format:
{{
  "ph_rule": "ActualDate" | "AcrossMidnight",
  "rates": [
    {{
      "name": "PHOL1",
      "factor": <float>,
      "description": "string"
    }}
  ],
  "clause_references": ["Clause X.Y"]
}}

Award: {award_name}

Relevant clauses:
{clauses}

Extract the public holiday rules as JSON:"""

BREAK_RULES_PROMPT = """Extract break and meal penalty rules from the following award clauses.

Output JSON format:
{{
  "auto_break_after_hours": <float> or null,
  "auto_break_length": <float> or null,
  "max_missed_break": <float> or null,
  "meal_penalty_enabled": <boolean>,
  "meal_penalty_factor": <float> or null,
  "clause_references": ["Clause X.Y"]
}}

Award: {award_name}

Relevant clauses:
{clauses}

Extract the break rules as JSON:"""

ALLOWANCES_PROMPT = """Extract allowances from the following award clauses.

Output JSON format:
{{
  "allowances": [
    {{
      "name": "FIRST_AID",
      "type": "CLAIMABLE" | "THRESHOLD" | "HOURLY" | "DAILY",
      "threshold": <float> or null,
      "weekly_max": <int> or null,
      "applies_to_days": ["Weekday", "Saturday", "Sunday"],
      "clause_references": ["Clause X.Y"]
    }}
  ]
}}

Award: {award_name}

Relevant clauses:
{clauses}

Extract the allowances as JSON:"""

COMPLETE_AWARD_EXTRACTION_PROMPT = """Extract ALL wage calculation rules from the following award clauses in a single comprehensive response.

Award Details:
- Name: {award_name}
- ID: {award_id}
- Source: {source_url}

Extract ALL of the following rule categories:

1. **Ordinary Hours**: Standard work hours, span, daily thresholds
2. **Overtime Rules**: All overtime triggers, factors, thresholds
3. **Weekend Penalties**: Saturday and Sunday penalty rates
4. **Public Holiday Rules**: Public holiday handling and rates
5. **Break Rules**: Break requirements and meal penalties
6. **Allowances**: All allowances and reimbursements

Relevant Award Clauses:
--- 
{clauses}
--- 

Extract complete award specification with all rule categories filled out. Use null for missing optional fields."""

GAP_ANALYSIS_PROMPT = """Compare the new award rules against the current system configuration and identify gaps.

New Award Rules:
{award_spec}

Current System Configuration:
{current_config}

Identify gaps in the following categories:

1. **Config-Only Gaps**: Changes that only require JSON configuration updates
   - Rate factor changes
   - Threshold changes
   - Max/min value changes
   - New allowances with existing types

2. **Code-Required Gaps**: Changes that require Python engine modifications
   - New calculation logic
   - New rule types
   - Unsupported employment types
   - New penalty structures

3. **Ambiguous Items**: Items that need human clarification
   - Vague language
   - Missing specifications
   - Conflicting clauses

Output JSON format:
{{
  "gaps": {{
    "config_only": [
      {{
        "category": "overtime_rules",
        "severity": "low" | "medium" | "high",
        "description": "string",
        "current_value": <any>,
        "required_value": <any>,
        "json_path": "AwardVariationRates[Name=OT1].DailyMax",
        "clause_reference": "Clause X.Y"
      }}
    ],
    "code_required": [
      {{
        "category": "break_rules",
        "severity": "low" | "medium" | "high",
        "description": "string",
        "current_capability": "string",
        "required_capability": "string",
        "affected_functions": ["calculate_pay_for_shift"],
        "clause_reference": "Clause X.Y"
      }}
    ],
    "ambiguous": [
      {{
        "category": "public_holiday_rules",
        "severity": "low" | "medium" | "high",
        "description": "string",
        "clause_text": "string",
        "clause_reference": "Clause X.Y",
        "possible_interpretations": ["interpretation 1", "interpretation 2"]
      }}
    ]
  }}
}}

Analyze and output gaps as JSON:"""

PATCH_PLAN_PROMPT = """Generate a detailed Python patch plan for the identified code-required gaps.

# Gap Report
{gap_report}

# Award Specification
{award_spec}

# Python Code File Outline
{file_outline}

# Affected Functions (Current Implementation)
{affected_functions}

# Additional Context (Related Functions)
{related_context}

---

## Instructions

You are analyzing an existing Python wage calculation script that needs to be updated to implement new award rules.

**Your task:**
1. Review each code-required gap and understand what needs to change
2. Examine the current implementation of affected functions
3. Design specific code modifications (pseudocode) with exact function names
4. Provide detailed explanations for each change

**Output Format (Markdown):**

# Python Patch Plan: [Award Name]

## Executive Summary
- Total code changes required: [number]
- Affected functions: [list]
- Estimated complexity: [Low/Medium/High]
- Risk assessment: [impact analysis]

## Changes Overview
[Table of all changes with severity, function, and description]

---

## Change #1: [Description]

**Gap ID:** [gap_id]
**Severity:** [high/medium/low]
**Affected Function:** `function_name` (Lines X-Y)
**Clause Reference:** [Clause X.Y]

### Current Behavior
[Explain what the current code does]

```python
# Current code (Lines X-Y)
[paste current implementation]
```

### Required Behavior
[Explain what the award requires]

### Proposed Solution

**Approach:** [High-level strategy]

**Modified Code:**
```python
# Modified code (Lines X-Y)
[complete replacement code with comments]
```

**Key Changes:**
- [Bullet point list of specific changes]

**Edge Cases Handled:**
- [List edge cases and how they're handled]

### Dependencies
[Any other functions that need to be updated or are affected]

---

## Change #2: [Next change]
...

---

## Implementation Checklist
- [ ] Update function: `function_name_1`
- [ ] Update function: `function_name_2`
- [ ] Add new helper function: `helper_name` (if needed)
- [ ] Validate with sample shifts

## Risk Mitigation
- **Backward compatibility:** [concerns and solutions]
- **Edge cases:** [unusual scenarios to test]
- **Performance impact:** [assessment]

## Validation Strategy
1. [Step 1 to validate changes]
2. [Step 2 to validate changes]
3. [Final integration test]

---

**IMPORTANT:**
- Maintain existing code style and naming conventions
- Preserve all existing functionality that's not being changed
- Add inline comments explaining non-obvious logic
- Consider backward compatibility with existing data

Generate the complete patch plan (markdown) now:"""
