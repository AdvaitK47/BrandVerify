
"""
Text Compliance & Claim Verification Service.

Flags potentially risky marketing claims for human review.
These rules are heuristic checks, not legal determinations.
"""

import re
from typing import List, Optional

from backend.models.scan import ComplianceFlag, SeverityLevel, ScanDiffItem
from backend.services.brand_rules import load_rules
from backend.services.rule_models import RuleSet


def verify_text_compliance(
    text: str,
    custom_rule: Optional[str] = None,
    rules: Optional[RuleSet] = None,
) -> ScanDiffItem:
    """Flag possible issues and provide cautious, evidence-aware suggestions."""

    if rules is None:
        rules = load_rules(None)

    flags: List[ComplianceFlag] = []
    modified_text = text

    # Check potentially risky claims.
    for idx, claim in enumerate(rules.claims):
        pattern, title, fix = claim.pattern, claim.title, claim.fix
        match = re.search(pattern, text, re.IGNORECASE)

        if not match:
            continue

        original_phrase = match.group(0)

        severity = SeverityLevel(claim.severity)

        flags.append(
            ComplianceFlag(
                id=f"flag-text-{idx + 1}",
                rule_citation=(
                    "BrandVerify heuristic claim check; "
                    "human review and substantiation may be needed"
                ),
                flag_type="claim_substantiation",
                severity=severity,
                title=title,
                description=(
                    f'The copy uses the claim "{original_phrase}". '
                    "The scan cannot verify whether it is accurate. "
                    "Check supporting evidence and applicable requirements "
                    "before publishing; this flag is not a legal determination."
                ),
                original_snippet=original_phrase,
                recommended_fix=fix,
                status="pending",
            )
        )

        # Replace only the first occurrence in the proposed draft.
        # These are cautious suggestions, not verified factual claims.
        modified_text = re.sub(
            pattern,
            lambda m: f"{m.group(0)} [REVIEW: {fix}]",
            modified_text,
            count=1,
            flags=re.IGNORECASE,
        )

    # A custom rule was supplied, but this simple implementation does not
    # semantically verify whether the copy satisfies that rule.
    if custom_rule and custom_rule.strip():
        flags.append(
            ComplianceFlag(
                id="flag-custom-rule",
                rule_citation="User-provided custom rule",
                flag_type="custom_rule",
                severity=SeverityLevel.INFO,
                title="Custom Rule Requires Review",
                description=(
                    f'The scan received this custom constraint: '
                    f'"{custom_rule[:300]}". '
                    "This version does not independently verify semantic "
                    "compliance with the custom rule."
                ),
                original_snippet=text[:80] + ("..." if len(text) > 80 else ""),
                recommended_fix=(
                    "Review the content against the custom rule manually."
                ),
                status="pending",
            )
        )

    # Do not add invented benchmark footnotes or imply tests were conducted.
    return ScanDiffItem(
        original_text=text,
        recommended_text=modified_text,
        flags=flags,
    )
