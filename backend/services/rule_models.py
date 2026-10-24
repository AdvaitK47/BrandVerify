"""
Plain data types for brand rule sets (loaded from backend/rules/*.json).
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ClaimRule:
    id: str
    pattern: str      # regex: a claim that may need substantiation
    title: str
    fix: str
    severity: str     # "info", "warning" or "critical"


@dataclass(frozen=True)
class DisclaimerRule:
    id: str
    title: str
    trigger: str      # regex: language that makes the disclaimer expected
    accepted: str     # regex: wording that counts as the disclaimer
    fix: str


@dataclass(frozen=True)
class RuleSet:
    brand_id: str     # which rule file was used ("default" if no brand file)
    name: str
    claims: Tuple[ClaimRule, ...]
    disclaimers: Tuple[DisclaimerRule, ...]
