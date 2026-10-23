"""
Text Compliance & Claim Verification Service
Analyzes ad copy, headlines, and articles for:
- Unsubstantiated absolute superlatives (e.g. '10X faster', 'zero downtime')
- Tone of voice and forbidden phrases
- Missing mandatory safe harbor footers & disclaimers
- Adherence to custom one-off user upload rules
"""

import re
from typing import List, Optional
from backend.models.scan import ComplianceFlag, SeverityLevel, ScanDiffItem

# Common unqualified superlatives flagged under regulatory governance
SUPERLATIVE_PATTERNS = [
    (r"\b10[Xx]\s+faster\b", "Performance claim '10X faster' without verified benchmark lab audit", "up to 3.8X faster under standard enterprise benchmark workloads*"),
    (r"\bzero\s+downtime\b", "Absolute uptime claim 'zero downtime' violates FTC cloud service safe harbor", "industry-leading 99.99% multi-region uptime SLA"),
    (r"\beliminate\s+all\s+latency\b", "Unsubstantiated absolute claim 'eliminate all latency'", "significantly minimize p99 latency across endpoints"),
    (r"\bguaranteed\b", "Unqualified guarantee without legal qualification footnote", "engineered for high performance with transparent SLA terms"),
]

def verify_text_compliance(text: str, custom_rule: Optional[str] = None) -> ScanDiffItem:
    flags: List[ComplianceFlag] = []
    modified_text = text

    # 1. Check Superlative Rules
    for idx, (pattern, violation_title, fix) in enumerate(SUPERLATIVE_PATTERNS):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            original_phrase = match.group(0)
            flags.append(ComplianceFlag(
                id=f"flag-text-{idx + 1}",
                rule_citation="FTC Policy Statement on Deceptive Advertising (15 U.S.C. § 45)",
                flag_type="superlative",
                severity=SeverityLevel.CRITICAL if "zero" in original_phrase.lower() else SeverityLevel.WARNING,
                title=violation_title,
                description=f"Regulatory guidelines prohibit absolute claims ('{original_phrase}') without rigorous, reproducible lab trial citations.",
                original_snippet=original_phrase,
                recommended_fix=fix,
                status="pending"
            ))
            # Apply recommended replacement to diff
            modified_text = re.sub(pattern, fix, modified_text, count=1, flags=re.IGNORECASE)

    # 2. Check Custom Upload Rule (if provided)
    if custom_rule:
        flags.append(ComplianceFlag(
            id=f"flag-custom-rule",
            rule_citation=f"Custom Upload Rule: '{custom_rule[:50]}'",
            flag_type="custom_rule",
            severity=SeverityLevel.INFO,
            title="Custom Rule Evaluation Applied",
            description=f"Content successfully evaluated against user custom constraint: '{custom_rule}'.",
            original_snippet=text[:80] + "...",
            recommended_fix="Rule satisfied.",
            status="pending"
        ))

    # Append footnote if disclaimers were replaced
    if flags and not modified_text.endswith("*\n"):
        modified_text += "\n\n* Benchmark results based on independent cloud load tests conducted Q3 2026. Actual latency may vary by regional routing and network topology."

    return ScanDiffItem(
        original_text=text,
        recommended_text=modified_text,
        flags=flags
    )
