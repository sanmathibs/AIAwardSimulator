"""
LLM-based JSON configuration generator using structured outputs
"""

import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from utils.openai_client import OpenAIClient
from models import AwardSpec


# Pydantic models for structured JSON generation
class AwardVariationConfig(BaseModel):
    """Award variation configuration - flexible to accept additional fields"""

    model_config = {"extra": "allow"}  # Allow additional fields not in baseline

    AwardVariationName: str
    MaxMissedBreak: float
    MinimumEngagement: Optional[float] = None
    MinBreakBetweenShifts: float = 10.0
    DailyHoursThreshold: float
    SpanOfHoursStart: str
    SpanOfHoursEnd: str
    IncludeWeekendsInSpan: bool = True
    PhRule: str = "ActualDate"
    OvernightRule: str = "AcrossMidnight"
    AutoBreakAfterHours: float
    AutoBreakLength: float
    ChargingModel: str = "Fixed"
    RateModel: str = "Factored"
    SetNonScheduledHoursToOT: bool = False
    AnnualLeaveLoadingMode: str = "Simple"
    EnableBrokenShift: bool = False
    RDO_CycleDays: Optional[int] = None
    RDO_HoursPerDay: Optional[float] = None
    EnableRDOAccrual: bool = False
    PayModel: str = "BaseRateFTM"


class AwardVariationRate(BaseModel):
    """Individual rate configuration - flexible to accept additional fields"""

    model_config = {"extra": "allow"}  # Allow additional fields for novel rate types

    AwardVariationName: str
    AwardId: str
    Name: str
    DailyMax: Optional[float] = None
    Weeklymax: Optional[float] = None
    Factor: Optional[float] = None
    Threshold: Optional[float] = None
    IsTaxable: bool = True
    IsSuperable: bool = True
    IsPayrollTax: bool = True
    IsWic: bool = True
    IsInvoice: bool = False
    IsOnCost: bool = False
    AllowanceType: Optional[str] = None
    OnCostContributionPercentage: float = 100.0
    DayOfWeek: Optional[str] = None
    StartHour: Optional[str] = None
    EndHour: Optional[str] = None
    IncludeHour: Optional[str] = None
    DailyMin: Optional[float] = None


class RateProperty(BaseModel):
    """Rate property configuration - flexible to accept additional fields"""

    model_config = {"extra": "allow"}  # Allow additional properties

    Name: str
    IsTaxable: bool = True
    IsSuperable: bool = True
    IsPayrollTax: bool = True
    IsWic: bool = True
    IsInvoice: bool = False


class ShiftRule(BaseModel):
    """Shift rule configuration - flexible to accept additional fields"""

    model_config = {"extra": "allow"}  # Allow additional shift constraints

    AwardVariationId: str
    Name: str
    DayOfWeek: str
    StartHour: List[str]
    EndHour: List[str]


class ShiftRules(BaseModel):
    """Container for shift rules"""

    Rules: List[ShiftRule]


class CompleteConfig(BaseModel):
    """Complete JSON configuration structure"""

    AwardVariation: List[AwardVariationConfig]
    AwardVariationRates: List[AwardVariationRate]
    RateProperties: List[RateProperty]
    Shift_Rules: ShiftRules


class ConfigGeneratorLLM:
    """Generate JSON configuration using LLM with structured outputs"""

    def __init__(self, openai_client: Optional[OpenAIClient] = None):
        self.openai_client = openai_client or OpenAIClient()

    def generate(
        self, award_spec: AwardSpec, baseline_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate complete JSON configuration using LLM

        Args:
            award_spec: Extracted award specification (Pydantic model)
            baseline_config: Baseline configuration to use as reference

        Returns:
            Complete configuration dict
        """
        # Create prompt with award spec and baseline example
        prompt = self._create_generation_prompt(award_spec, baseline_config)

        # Use structured output to generate config
        config_response = self.openai_client.chat_completion_structured(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at generating wage calculation system configurations from Fair Work award specifications. Generate accurate, complete JSON configurations that properly implement all award rules.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format=CompleteConfig,
        )

        # Convert Pydantic model to dict
        generated_config = config_response.model_dump()

        # Merge with baseline for fields we don't generate
        complete_config = {
            "Shifts": baseline_config.get("Shifts", []),
            "AwardVariation": generated_config["AwardVariation"],
            "AwardVariationRates": generated_config["AwardVariationRates"],
            "Rates": baseline_config.get("Rates", []),
            "RateProperties": generated_config["RateProperties"],
            "Shift_Rules": generated_config["Shift_Rules"],
            "PublicHolidays": baseline_config.get("PublicHolidays", []),
        }

        return complete_config

    def _create_generation_prompt(
        self, award_spec: AwardSpec, baseline_config: Dict[str, Any]
    ) -> str:
        """Create comprehensive prompt for config generation"""

        # Get baseline examples for reference
        baseline_award_var = baseline_config.get("AwardVariation", [{}])[0]
        baseline_rates = baseline_config.get("AwardVariationRates", [])[:3]
        baseline_shift_rules = baseline_config.get("Shift_Rules", {}).get("Rules", [])[
            :2
        ]

        prompt = f"""Generate a complete wage calculation system configuration based on the following Fair Work award specification.

# Award Specification

Award Name: {award_spec.award_name}
Award ID: {award_spec.award_id}

## Ordinary Hours
{json.dumps(award_spec.ordinary_hours.model_dump() if award_spec.ordinary_hours else {}, indent=2)}

## Overtime Rules
{json.dumps([ot.model_dump() for ot in award_spec.overtime_rules], indent=2)}

## Weekend Penalties
{json.dumps([wp.model_dump() for wp in award_spec.weekend_penalties], indent=2)}

## Public Holiday Rules
{json.dumps(award_spec.public_holiday_rules.model_dump() if award_spec.public_holiday_rules else {}, indent=2)}

## Break Rules
{json.dumps(award_spec.break_rules.model_dump() if award_spec.break_rules else {}, indent=2)}

## Allowances
{json.dumps([a.model_dump() for a in award_spec.allowances], indent=2)}

# Reference Baseline Configuration

Here are examples from the baseline configuration to understand the structure and conventions:

## Example AwardVariation:
{json.dumps(baseline_award_var, indent=2)}

## Example AwardVariationRates (first 3):
{json.dumps(baseline_rates, indent=2)}

## Example Shift_Rules (first 2):
{json.dumps(baseline_shift_rules, indent=2)}

# Generation Instructions

Generate a complete configuration with:

1. **AwardVariation** (array with 1 item):
   - Use award specifications to populate all fields
   - DailyHoursThreshold from ordinary_hours.daily_threshold
   - SpanOfHoursStart/End from ordinary_hours.span_of_hours
   - MaxMissedBreak, AutoBreakAfterHours, AutoBreakLength from break_rules
   - PhRule from public_holiday_rules.ph_rule
   - Use sensible defaults for fields not in spec (e.g., MinBreakBetweenShifts=10.0, ChargingModel="Fixed", RateModel="Factored")
   - **IMPORTANT**: If this award has unique features not in the baseline (e.g., shift loading patterns, special calculation rules, industry-specific requirements), ADD NEW FIELDS with descriptive names (e.g., "ShiftLoadingEnabled", "MinimumCallOutHours", "TravelTimeMultiplier", etc.)

2. **AwardVariationRates** (array):
   - First rate: "DAY1" for ordinary hours (Factor=1.0, DailyMax from ordinary_hours)
   - Overtime rates: One entry per overtime_rule (use rule name, factor, thresholds)
   - Weekend rates: One entry per weekend_penalty (use day, factor)
   - Public holiday rates: Based on public_holiday_rules.rates
   - Allowances: One entry per allowance (set AllowanceType field, handle THRESHOLD type specially)
   - Generate unique AwardId for each rate (use uuid format)
   - Set tax/super flags appropriately (Ordinary/OT/Weekend/PH: taxable+superable; Allowances: taxable only for non-THRESHOLD types)
   - **IMPORTANT**: If this award has special rate types not in baseline (e.g., "On-Call", "Standby", "Recall", "Split Shift", "Broken Shift", "Training Rate"), CREATE NEW RATE ENTRIES with appropriate names and properties
   - **FLEXIBILITY**: Add extra fields if needed (e.g., "MinimumPaymentHours", "CallOutRate", "CompensationDays", "AccrualRate") to capture unique award requirements

3. **RateProperties** (array):
   - One entry per unique rate name (DAY1, OT1, OT2, SAT1, SUN1, PHOL1, etc.)
   - Standard tax properties for each type
   - **ADAPTIVE**: If new rate types were created in AwardVariationRates, include corresponding RateProperty entries with appropriate tax/super settings

4. **Shift_Rules** (object with Rules array):
   - DAY1 rule for Weekday (all hours: 00:00-23:59)
   - Weekend rules matching weekend_penalties
   - PHOL1 rule for Public Holiday
   - Use award name as AwardVariationId
   - **NOVEL PATTERNS**: If the award specifies special shift patterns (e.g., afternoon shift loading, night shift differentials, rotating roster penalties), ADD SHIFT RULES with appropriate time ranges and names (e.g., "AFTERNOON1", "NIGHT1", "ROTATING1")

# CRITICAL: Award Flexibility & Adaptation

This award may have unique characteristics not present in the baseline. You MUST:

✅ **Identify Novel Features**: Look for:
   - Unique payment structures (e.g., piece rates, commission, productivity bonuses)
   - Special allowances (e.g., tool allowance, vehicle allowance, uniform, meal breaks)
   - Industry-specific rules (e.g., sleepover, residential, on-site, remote work)
   - Loading patterns (e.g., shift loading, roster loading, higher duties)
   - Time-based differentials (e.g., afternoon/night shift, rotating rosters)
   - Call-out/recall provisions
   - Split/broken shift arrangements
   - Training or apprentice rates
   - Accrual rules (e.g., RDO accrual, time-in-lieu)

✅ **Create New Fields**: When you find unique features:
   - Add descriptive fields to AwardVariation (e.g., "EnableShiftLoading": true, "ShiftLoadingPercentage": 15.0)
   - Create new rate entries in AwardVariationRates with appropriate names
   - Add extra properties that capture the specific requirement
   - Use clear, self-documenting field names

✅ **Preserve Baseline Structure**: 
   - Keep all standard fields from baseline
   - Only ADD fields, never remove standard ones
   - Maintain naming conventions where possible
   - Ensure backward compatibility

✅ **Documentation in Field Names**:
   - Use descriptive names: "MinimumCallOutHours" not "MCH"
   - Be explicit: "FirstAidAllowancePerDay" not "Allowance1"
   - Follow patterns: "Enable[Feature]", "Minimum[Item]", "[Item]Percentage"

IMPORTANT:
- Maintain consistent naming (DAY1, OT1, OT2, SAT1, SAT2, SUN1, PHOL1, etc.)
- All rates must have corresponding RateProperty and Shift_Rule entries
- Use proper data types (floats for hours/factors, bools for flags, strings for names)
- Ensure DayOfWeek values are: "Weekday", "Saturday", "Sunday", or "Public Holiday"
- StartHour/EndHour in Shift_Rules must be arrays of strings in HH:MM format
- **NEW FIELDS**: Use camelCase, descriptive names, appropriate types
- **EXTENSIBILITY**: The configuration must be flexible enough to fully implement ALL award requirements, even if they're unusual
"""

        return prompt
