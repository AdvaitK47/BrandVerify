"""
Required-disclaimer check for documents.

Some kinds of statements normally need a standard disclaimer nearby, for
example forward-looking statements or investment returns. Each rule below
has a TRIGGER (language that makes the disclaimer expected) and an ACCEPTED
pattern (wording that counts as the disclaimer being present). If the
trigger is found and no accepted wording appears anywhere in the document
(body, tables, headers or footers), a flag is raised.

These are heuristic checks for human review, not legal determinations.
"""

import re
from dataclasses import dataclass
from typing import List

from backend.models.scan import ComplianceFlag, SeverityLevel


@dataclass(frozen=True)
class DisclaimerRule:
    key: str
    title: str
    trigger: str      # regex: language that makes the disclaimer expected
    accepted: str     # regex: wording that counts as the disclaimer
    fix: str


DISCLAIMER_RULES = [
    DisclaimerRule(
        key="forward-looking",
        title="Missing Forward-Looking Statements Disclaimer",
        trigger=(
            r"\b(we\s+expect|we\s+anticipate|we\s+project|projected|"
            r"forecasts?|expected\s+to\s+(?:grow|reach|increase|deliver)|"
            r"will\s+(?:grow|increase|reach|double|triple))\b"
        ),
        accepted=r"forward[-\s]looking",
        fix=(
            "Add a forward-looking statements disclaimer, using wording "
            "approved by your legal or compliance team."
        ),
    ),
    DisclaimerRule(
        key="past-performance",
        title="Missing Past Performance Disclaimer",
        trigger=(
            r"\b(annual(?:ized)?\s+returns?|expected\s+returns?|"
            r"investment\s+returns?|returns?\s+of\s+\d|\broi\b)"
        ),
        accepted=r"past\s+performance|results\s+may\s+vary",
        fix=(
            "Add a past performance disclaimer, using wording approved "
            "by your legal or compliance team."
        ),
    ),
]


def check_required_disclaimers(text: str) -> List[ComplianceFlag]:
    """Return one flag for each rule whose trigger is present but whose
    disclaimer wording is absent."""
    flags: List[ComplianceFlag] = []

    for rule in DISCLAIMER_RULES:
        trigger = re.search(rule.trigger, text, re.IGNORECASE)
        if not trigger:
            continue
        if re.search(rule.accepted, text, re.IGNORECASE):
            continue

        phrase = trigger.group(0)
        flags.append(
            ComplianceFlag(
                id=f"flag-disclaimer-{rule.key}",
                rule_citation=(
                    "BrandVerify heuristic disclaimer check; "
                    "human review may be needed"
                ),
                flag_type="missing_disclaimer",
                severity=SeverityLevel.WARNING,
                title=rule.title,
                description=(
                    f'The document uses language such as "{phrase}", which '
                    "usually needs a matching disclaimer, but no matching "
                    "disclaimer wording was found. This check is "
                    "heuristic and is not a legal determination."
                ),
                original_snippet=phrase,
                recommended_fix=rule.fix,
                status="pending",
            )
        )

    return flags
