from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class GraduationMode(str, Enum):
    ABRUPT = "abrupt"
    GRADUAL = "gradual"


@dataclass
class SocialWelfareConfig:
    enabled: bool = False
    benefit_per_capita: float = 5.0
    eligibility_threshold: float = 80.0
    max_beneficiaries_ratio: float = 0.4
    funding_tax_surcharge: float = 0.05
    condition_school_attendance: bool = True
    condition_health_checkup: bool = True
    graduation_income_threshold: float = 140.0
    graduation_grace_ticks: int = 10
    graduation_mode: str = "gradual"
    graduation_transition_band: float = 0.1
    conditionalities_enabled: bool = True
