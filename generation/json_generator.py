"""
JSON configuration generator
"""

import json
import uuid
from typing import Dict, Any, List
from datetime import datetime


class ConfigGenerator:
    """Generate JSON configuration from award spec"""

    def generate(
        self, award_spec: Dict[str, Any], baseline_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate complete JSON configuration

        Args:
            award_spec: Extracted award specification
            baseline_config: Baseline configuration to merge with

        Returns:
            Complete configuration dict
        """
        config = {
            "Shifts": baseline_config.get("Shifts", []),
            "AwardVariation": self._generate_award_variation(award_spec),
            "AwardVariationRates": self._generate_award_variation_rates(award_spec),
            "Rates": baseline_config.get("Rates", []),
            "RateProperties": self._generate_rate_properties(award_spec),
            "Shift_Rules": self._generate_shift_rules(award_spec),
            "PublicHolidays": baseline_config.get("PublicHolidays", []),
        }

        return config

    def _generate_award_variation(
        self, award_spec: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate AwardVariation configuration"""
        ordinary_hours = award_spec.get("ordinary_hours", {})
        break_rules = award_spec.get("break_rules", {})
        ph_rules = award_spec.get("public_holiday_rules", {})

        return [
            {
                "AwardVariationName": award_spec.get("award_name", "Unknown Award"),
                "MaxMissedBreak": break_rules.get("max_missed_break", 5.0),
                "MinimumEngagement": award_spec.get("minimum_engagement", {}).get(
                    "default"
                ),
                "MinBreakBetweenShifts": 10.0,
                "DailyHoursThreshold": ordinary_hours.get("daily_threshold", 10.0),
                "SpanOfHoursStart": ordinary_hours.get("span_of_hours", {})
                .get("weekday", {})
                .get("start", "06:00"),
                "SpanOfHoursEnd": ordinary_hours.get("span_of_hours", {})
                .get("weekday", {})
                .get("end", "18:00"),
                "IncludeWeekendsInSpan": True,
                "PhRule": ph_rules.get("ph_rule", "ActualDate"),
                "OvernightRule": "AcrossMidnight",
                "AutoBreakAfterHours": break_rules.get("auto_break_after_hours", 5.0),
                "AutoBreakLength": break_rules.get("auto_break_length", 0.5),
                "ChargingModel": "Fixed",
                "RateModel": "Factored",
                "SetNonScheduledHoursToOT": False,
                "AnnualLeaveLoadingMode": "Simple",
                "EnableBrokenShift": False,
                "RDO_CycleDays": None,
                "RDO_HoursPerDay": None,
                "EnableRDOAccrual": False,
                "PayModel": "BaseRateFTM",
            }
        ]

    def _generate_award_variation_rates(
        self, award_spec: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate AwardVariationRates configuration"""
        rates = []
        award_name = award_spec.get("award_name", "Unknown Award")
        ordinary_hours = award_spec.get("ordinary_hours", {})

        # DAY1 - Ordinary hours
        rates.append(
            {
                "AwardVariationName": award_name,
                "AwardId": str(uuid.uuid4()),
                "Name": "DAY1",
                "DailyMax": ordinary_hours.get("daily_threshold", 10.0),
                "Weeklymax": ordinary_hours.get("weekly_hours", 38.0),
                "Factor": 1.0,
                "Threshold": None,
                "IsTaxable": True,
                "IsSuperable": True,
                "IsPayrollTax": True,
                "IsWic": True,
                "IsInvoice": False,
                "IsOnCost": False,
                "AllowanceType": None,
                "OnCostContributionPercentage": 100.0,
                "DayOfWeek": None,
                "StartHour": None,
                "EndHour": None,
                "IncludeHour": None,
                "DailyMin": None,
            }
        )

        # Overtime rules
        for ot_rule in award_spec.get("overtime_rules", []):
            rates.append(
                {
                    "AwardVariationName": award_name,
                    "AwardId": str(uuid.uuid4()),
                    "Name": ot_rule.get("name", "OT1"),
                    "DailyMax": ot_rule.get("daily_max"),
                    "Weeklymax": ot_rule.get("weekly_max"),
                    "Factor": ot_rule.get("factor", 1.5),
                    "Threshold": ot_rule.get("threshold"),
                    "IsTaxable": True,
                    "IsSuperable": False,
                    "IsPayrollTax": True,
                    "IsWic": True,
                    "IsInvoice": False,
                    "IsOnCost": False,
                    "AllowanceType": None,
                    "OnCostContributionPercentage": 100.0,
                    "DayOfWeek": None,
                    "StartHour": None,
                    "EndHour": None,
                    "IncludeHour": None,
                    "DailyMin": None,
                }
            )

        # Weekend penalties
        for weekend in award_spec.get("weekend_penalties", []):
            rates.append(
                {
                    "AwardVariationName": award_name,
                    "AwardId": str(uuid.uuid4()),
                    "Name": weekend.get("name", "SAT1"),
                    "DailyMax": None,
                    "Weeklymax": None,
                    "Factor": weekend.get("factor", 1.5),
                    "Threshold": None,
                    "IsTaxable": True,
                    "IsSuperable": True,
                    "IsPayrollTax": True,
                    "IsWic": True,
                    "IsInvoice": False,
                    "IsOnCost": False,
                    "AllowanceType": None,
                    "OnCostContributionPercentage": 100.0,
                    "DayOfWeek": weekend.get("day", "Saturday"),
                    "StartHour": None,
                    "EndHour": None,
                    "IncludeHour": None,
                    "DailyMin": None,
                }
            )

        # Public holiday rates
        ph_rules = award_spec.get("public_holiday_rules", {})
        for ph_rate in ph_rules.get("rates", []):
            rates.append(
                {
                    "AwardVariationName": award_name,
                    "AwardId": str(uuid.uuid4()),
                    "Name": ph_rate.get("name", "PHOL1"),
                    "DailyMax": None,
                    "Weeklymax": None,
                    "Factor": ph_rate.get("factor", 2.0),
                    "Threshold": None,
                    "IsTaxable": True,
                    "IsSuperable": True,
                    "IsPayrollTax": True,
                    "IsWic": True,
                    "IsInvoice": False,
                    "IsOnCost": False,
                    "AllowanceType": None,
                    "OnCostContributionPercentage": 100.0,
                    "DayOfWeek": "Public Holiday",
                    "StartHour": None,
                    "EndHour": None,
                    "IncludeHour": None,
                    "DailyMin": None,
                }
            )

        # Allowances
        for allowance in award_spec.get("allowances", []):
            rates.append(
                {
                    "AwardVariationName": award_name,
                    "AwardId": str(uuid.uuid4()),
                    "Name": allowance.get("name", "ALLOWANCE"),
                    "DailyMax": None,
                    "Weeklymax": allowance.get("weekly_max"),
                    "Factor": None,
                    "Threshold": allowance.get("threshold"),
                    "IsTaxable": True,
                    "IsSuperable": allowance.get("type") != "THRESHOLD",
                    "IsPayrollTax": False,
                    "IsWic": False,
                    "IsInvoice": False,
                    "IsOnCost": False,
                    "AllowanceType": allowance.get("type"),
                    "OnCostContributionPercentage": 100.0,
                    "DayOfWeek": None,
                    "StartHour": None,
                    "EndHour": None,
                    "IncludeHour": None,
                    "DailyMin": None,
                }
            )

        return rates

    def _generate_rate_properties(
        self, award_spec: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate RateProperties configuration"""
        properties = []

        # Standard properties for common rates
        rate_configs = [
            ("DAY1", True, True, True, True, False),
            ("OT1", True, False, True, True, False),
            ("OT2", True, False, True, True, False),
            ("SAT1", True, True, True, True, False),
            ("SAT2", True, True, True, True, False),
            ("SUN1", True, True, True, True, False),
            ("PHOL1", True, True, True, True, False),
        ]

        for name, taxable, superable, payroll, wic, invoice in rate_configs:
            properties.append(
                {
                    "Name": name,
                    "IsTaxable": taxable,
                    "IsSuperable": superable,
                    "IsPayrollTax": payroll,
                    "IsWic": wic,
                    "IsInvoice": invoice,
                }
            )

        return properties

    def _generate_shift_rules(self, award_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Shift_Rules configuration"""
        rules = []
        award_name = award_spec.get("award_name", "Unknown Award")

        # Basic weekday rule
        rules.append(
            {
                "AwardVariationId": award_name,
                "Name": "DAY1",
                "DayOfWeek": "Weekday",
                "StartHour": ["00:00", "23:59"],
                "EndHour": ["00:00", "23:59"],
            }
        )

        # Weekend rules
        for weekend in award_spec.get("weekend_penalties", []):
            rules.append(
                {
                    "AwardVariationId": award_name,
                    "Name": weekend.get("name", "SAT1"),
                    "DayOfWeek": weekend.get("day", "Saturday"),
                    "StartHour": ["00:00", "23:59"],
                    "EndHour": ["00:00", "23:59"],
                }
            )

        # Public holiday rule
        rules.append(
            {
                "AwardVariationId": award_name,
                "Name": "PHOL1",
                "DayOfWeek": "Public Holiday",
                "StartHour": ["00:00", "23:59"],
                "EndHour": ["00:00", "23:59"],
            }
        )

        return {"Rules": rules}
