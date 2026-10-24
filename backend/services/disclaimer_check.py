"""
Required-disclaimer check for documents.

Some kinds of statements normally need a standard disclaimer nearby, for
example forward-looking statements or investment returns. Each brand's rule
file (backend/rules/<brand_id>.json) lists disclaimer rules. A rule has a
TRIGGER (language that makes the disclaimer expected) and an ACCEPTED
pattern (wording that counts as the disclaimer being present). If the
trigger is found and no accepted wording appears anywhere in the document
(body, tables, headers or footers), a flag is raised.

These are heuristic checks for human review, not legal determinations.
"""

import re
from typing import List, Optional

from backend.models.scan import ComplianceFlag, SeverityLevel
from backend.services.brand_rules import load_rules
from backend.services.rule_models import RuleSet


def check_required_disclaimers(
    text: str, rules: Optional[RuleSet] = None
) -> List[ComplianceFlag]:
    """Return one flag for each rule whose trigger is present but whose
    disclaimer wording is absent. Uses the default rules if none are given."""
    if rules is None:
        rules = load_rules(None)

    flags: List[ComplianceFlag] = []

    for rule in rules.disclaimers:
        trigger = re.search(rule.trigger, text, re.IGNORECASE)
        if not trigger:
            continue
        if re.search(rule.accepted, text, re.IGNORECASE):
            continue

        phrase = trigger.group(0)
        flags.append(
            ComplianceFlag(
                id=f"flag-disclaimer-{rule.id}",
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
