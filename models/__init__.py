"""
Data models for AI Award Interpreter
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field


class GeneralRule(BaseModel):
    """General rule definition"""

    name: str
    description: str
    clause_references: List[str] = Field(default_factory=list)


class GenericItem(BaseModel):
    """Generic item with name and description"""

    name: str
    description: str


class ValueItem(BaseModel):
    """Item with name and value"""

    name: str
    value: Any


class HourSpan(BaseModel):
    """Span of hours for a day"""

    name: str  # "weekday", "saturday", "sunday"
    start: str  # "HH:MM"
    end: str  # "HH:MM"


class OrdinaryHours(BaseModel):
    """Ordinary hours configuration"""

    weekly_hours: float
    span_of_hours: List[HourSpan] = Field(default_factory=list)  # List of HourSpan
    daily_threshold: Optional[float] = None
    clause_references: List[str] = Field(default_factory=list)


class OvertimeRule(BaseModel):
    """Overtime rule definition"""

    name: str
    trigger_type: str  # "daily_excess", "weekly_excess", "after_ot1", etc.
    factor: float
    threshold: Optional[float] = None
    daily_max: Optional[float] = None
    weekly_max: Optional[float] = None
    applies_to: List[str] = Field(default_factory=list)
    clause_references: List[str] = Field(default_factory=list)


class TimeRange(BaseModel):
    """Time range definition"""

    start: str  # "HH:MM"
    end: str  # "HH:MM"


class WeekendPenalty(BaseModel):
    """Weekend penalty rate"""

    name: str
    day: str
    factor: float
    time_range: List[TimeRange] = Field(default_factory=list)
    minimum_engagement: Optional[float] = None
    clause_references: List[str] = Field(default_factory=list)


class PublicHolidayRules(BaseModel):
    """Public holiday rules"""

    ph_rule: str = Field(
        default="ActualDate", description='"ActualDate" or "AcrossMidnight"'
    )
    rates: List[ValueItem] = Field(default_factory=list)
    clause_references: List[str] = Field(default_factory=list)


class BreakRules(BaseModel):
    """Break and meal penalty rules"""

    auto_break_after_hours: Optional[float] = None
    auto_break_length: Optional[float] = None
    max_missed_break: Optional[float] = None
    meal_penalty_enabled: bool = False
    meal_penalty_factor: Optional[float] = None
    clause_references: List[str] = Field(default_factory=list)


class Allowance(BaseModel):
    """Allowance definition"""

    name: str
    type: str  # "CLAIMABLE", "THRESHOLD", "HOURLY", etc.
    threshold: Optional[float] = None
    weekly_max: Optional[int] = None
    applies_to_days: List[str] = Field(default_factory=list)
    clause_references: List[str] = Field(default_factory=list)


class AwardSpec(BaseModel):
    """Complete award specification"""

    award_id: str
    award_name: str
    effective_date: str
    version: str
    source_url: str

    ordinary_hours: Optional[OrdinaryHours] = None
    overtime_rules: List[OvertimeRule] = Field(default_factory=list)
    weekend_penalties: List[WeekendPenalty] = Field(default_factory=list)
    public_holiday_rules: Optional[PublicHolidayRules] = None
    break_rules: Optional[BreakRules] = None
    allowances: List[Allowance] = Field(default_factory=list)

    part_time_rules: List[GeneralRule] = Field(default_factory=list)
    special_employment_types: List[GeneralRule] = Field(default_factory=list)
    minimum_engagement: List[GeneralRule] = Field(default_factory=list)

    clause_references: List[GenericItem] = Field(default_factory=list)
    raw_metadata: List[GenericItem] = Field(default_factory=list)


@dataclass
class Gap:
    """Individual gap identified in analysis"""

    gap_id: str
    category: str
    severity: str  # "low", "medium", "high"
    gap_type: str  # "config_only", "code_required", "ambiguous"
    description: str
    current_value: Any = None
    required_value: Any = None
    json_path: Optional[str] = None
    affected_functions: List[str] = field(default_factory=list)
    clause_reference: Optional[str] = None
    clause_text: Optional[str] = None
    possible_interpretations: List[str] = field(default_factory=list)
    user_input_required: bool = False


@dataclass
class GapReport:
    """Complete gap analysis report"""

    analysis_id: str
    award_id: str
    timestamp: str

    gaps: Dict[str, List[Gap]] = field(
        default_factory=lambda: {
            "config_only": [],
            "code_required": [],
            "ambiguous": [],
        }
    )

    summary: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionState:
    """Session state for tracking progress"""

    session_id: str
    created_at: datetime
    status: str

    input: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, str] = field(default_factory=dict)
    ambiguities_resolved: Dict[str, Any] = field(default_factory=dict)
    vector_store_id: Optional[str] = None

    cost_breakdown: Dict[str, float] = field(default_factory=dict)
    total_cost: float = 0.0
