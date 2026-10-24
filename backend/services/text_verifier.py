
"""
Text Compliance & Claim Verification Service.

Checks risky marketing claims and supported rules extracted from a brand
rulebook. Findings are preliminary and are not legal determinations.
"""

import re
from typing import List, Optional

from backend.models.scan import ComplianceFlag, SeverityLevel, ScanDiffItem


CLAIM_PATTERNS = [
    (
        r"\b10[Xx]\s+faster\b",
        "Specific comparative performance claim needs substantiation",
        "a measured performance improvement supported by verified evidence",
    ),
    (
        r"\bzero\s+downtime\b",
        "Absolute uptime claim needs substantiation",
        "verified uptime performance under the applicable service terms",
    ),
    (
        r"\beliminate\s+all\s+latency\b",
        "Absolute latency claim needs substantiation",
        "measured latency improvements supported by verified evidence",
    ),
    (
        r"\b100%\s+bug[- ]free\b",
        "Absolute bug-free claim needs substantiation",
        "software quality supported by verified testing results",
    ),
    (
        r"\bguaranteed\b",
        "Guarantee language may need supporting terms and evidence",
        "terms and conditions supported by verified evidence",
    ),
]


def _extract_prohibited_phrases(rulebook_text: str) -> List[str]:
    """Extract prohibited phrases from supported rulebook formats."""
    phrases = []
    pattern = r"\bdo\s+not\s+claim\s*[“\"']?([^”\"'\n.]+)"

    for match in re.finditer(pattern, rulebook_text, re.IGNORECASE):
        phrase = match.group(1).strip().strip('•-* \t\r\n“”"\'')
        phrase = re.sub(r"[.]+$", "", phrase).strip()

        if phrase and phrase.casefold() not in {
            existing.casefold() for existing in phrases
        }:
            phrases.append(phrase)

    return phrases


def _extract_mandatory_disclaimer(
    rulebook_text: str,
) -> Optional[str]:
    """Extract mandatory disclaimer wording from the rulebook."""
    patterns = [
        r'\bbenchmark claims must include\s*:\s*["“](.+?)["”]',
        r'\bmandatory disclaimer\s*:\s*["“](.+?)["”]',
        r'\bmust include\s*:\s*["“](.+?)["”]',
    ]

    for pattern in patterns:
        match = re.search(
            pattern, rulebook_text, re.IGNORECASE | re.DOTALL
        )
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip()

    return None


def verify_text_compliance(
    text: str,
    custom_rule: Optional[str] = None,
    brand_rules_text: Optional[str] = None,
) -> ScanDiffItem:
    """Run general claim checks and supported brand-specific checks."""

    flags: List[ComplianceFlag] = []
    modified_text = text
    next_id = 1

    # 1. General risky-claim checks.
    for pattern, title, replacement in CLAIM_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue

        phrase = match.group(0)
        severity = (
            SeverityLevel.CRITICAL
            if "zero" in phrase.lower()
            else SeverityLevel.WARNING
        )

        flags.append(
            ComplianceFlag(
                id=f"flag-text-{next_id}",
                rule_citation=(
                    "BrandVerify heuristic claim check; "
                    "human review and substantiation may be needed"
                ),
                flag_type="claim_substantiation",
                severity=severity,
                title=title,
                description=(
                    f'The copy uses the claim "{phrase}". Its accuracy '
                    "has not been verified. Review supporting evidence "
                    "before publishing. This is not a legal determination."
                ),
                original_snippet=phrase,
                recommended_fix=f"Consider replacing with: {replacement}",
                status="pending",
            )
        )
        next_id += 1

        modified_text = re.sub(
            pattern,
            replacement,
            modified_text,
            count=1,
            flags=re.IGNORECASE,
        )

    # 2. Brand-specific prohibited phrases.
    if brand_rules_text and brand_rules_text.strip():
        for phrase in _extract_prohibited_phrases(brand_rules_text):
            match = re.search(re.escape(phrase), text, re.IGNORECASE)
            if not match:
                continue

            original_phrase = match.group(0)

            flags.append(
                ComplianceFlag(
                    id=f"flag-brand-prohibited-{next_id}",
                    rule_citation="Uploaded brand rulebook: prohibited claim",
                    flag_type="brand_rule",
                    severity=SeverityLevel.WARNING,
                    title="Claim Listed as Prohibited by Brand Rulebook",
                    description=(
                        f'The uploaded rulebook says not to use "{phrase}". '
                        "The submitted copy contains this phrase. "
                        "Review the brand requirement before publishing."
                    ),
                    original_snippet=original_phrase,
                    recommended_fix=(
                        "Remove the prohibited claim or use wording "
                        "approved by the brand reviewer."
                    ),
                    status="pending",
                )
            )
            next_id += 1

    # 3. Check for a missing mandatory disclaimer.
    if brand_rules_text and brand_rules_text.strip():
        disclaimer = _extract_mandatory_disclaimer(brand_rules_text)
        performance_match = re.search(
            r"\b(benchmark|benchmarks|benchmarking|faster)\b",
            text,
            re.IGNORECASE,
        )

        if (
            disclaimer
            and performance_match
            and disclaimer.casefold() not in text.casefold()
        ):
            flags.append(
                ComplianceFlag(
                    id="flag-brand-disclaimer-missing",
                    rule_citation=(
                        "Uploaded brand rulebook: mandatory disclaimer"
                    ),
                    flag_type="brand_rule",
                    severity=SeverityLevel.WARNING,
                    title="Mandatory Brand Disclaimer May Be Missing",
                    description=(
                        "The copy contains a performance-related claim, "
                        "but the required disclaimer from the uploaded "
                        "rulebook was not found."
                    ),
                    original_snippet=performance_match.group(0),
                    recommended_fix=f'Add the required disclaimer: "{disclaimer}"',
                    status="pending",
                )
            )

    # 4. Custom rules are informational until semantic checks are added.
    if custom_rule and custom_rule.strip():
        flags.append(
            ComplianceFlag(
                id="flag-custom-rule",
                rule_citation="User-provided custom rule",
                flag_type="custom_rule",
                severity=SeverityLevel.INFO,
                title="Custom Rule Requires Review",
                description=(
                    f'The scan received this constraint: "{custom_rule[:300]}". '
                    "Automatic semantic verification of custom rules "
                    "is not implemented."
                ),
                original_snippet=text[:80] + ("..." if len(text) > 80 else ""),
                recommended_fix=(
                    "Review the content against the custom rule manually."
                ),
                status="pending",
            )
        )

    # 5. Give the user a clean review instruction rather than a broken sentence.
    recommended_text = (
        "Please review the flagged claims, replace prohibited wording "
        "with brand-approved language, and add any required disclaimer."
        if flags
        else text
    )

    return ScanDiffItem(
        original_text=text,
        recommended_text=recommended_text,
        flags=flags,
    )
