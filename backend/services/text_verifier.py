
"""
Text Compliance & Claim Verification Service.

Flags potentially risky marketing claims for human review.
These rules are heuristic checks, not legal determinations.
"""

import re
from typing import List, Optional

from backend.models.scan import ComplianceFlag, SeverityLevel, ScanDiffItem


# Patterns identify claims that may need substantiation.
# Suggested replacements deliberately avoid unsupported statistics.
CLAIM_PATTERNS = [
    (
        r"\b10[Xx]\s+faster\b",
        "Specific comparative performance claim needs substantiation",
        "Describe the measured performance improvement, with verified evidence",
    ),
    (
        r"\bzero\s+downtime\b",
        "Absolute uptime claim needs substantiation",
        "Describe verified uptime performance and applicable service terms",
    ),
    (
        r"\beliminate\s+all\s+latency\b",
        "Absolute latency claim needs substantiation",
        "Describe measured latency improvements, with verified evidence",
    ),
    (
        r"\bguaranteed\b",
        "Guarantee language may need supporting terms and evidence",
        "Specify the actual guarantee terms, if one exists",
    ),
]


def verify_text_compliance(
    text: str,
    custom_rule: Optional[str] = None,
) -> ScanDiffItem:
    """Flag possible issues and provide cautious, evidence-aware suggestions."""

    flags: List[ComplianceFlag] = []
    modified_text = text

    # Check potentially risky claims.
    for idx, (pattern, title, fix) in enumerate(CLAIM_PATTERNS):
        match = re.search(pattern, text, re.IGNORECASE)

        if not match:
            continue

        original_phrase = match.group(0)

        severity = (
            SeverityLevel.CRITICAL
            if "zero" in original_phrase.lower()
            else SeverityLevel.WARNING
        )

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
            fix,
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
