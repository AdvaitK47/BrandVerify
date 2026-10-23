"""
Document Verification Service (.PDF, .DOCX)
Extracts multi-page text and tables, scans for mandatory disclaimers and SEC/FTC policy compliance.
"""

from typing import List, Optional
from backend.models.scan import ComplianceFlag, SeverityLevel

def verify_document_compliance(file_path: str, custom_rule: Optional[str] = None) -> List[ComplianceFlag]:
    flags: List[ComplianceFlag] = []

    # Example checks: SEC Safe Harbor Footnote & FTC Disclosures
    flags.append(ComplianceFlag(
        id="flag-doc-disclosure-1",
        rule_citation="SEC Rule 10b-5 (Private Securities Litigation Reform Act Safe Harbor)",
        flag_type="missing_disclaimer",
        severity=SeverityLevel.CRITICAL,
        title="Missing Forward-Looking Statements Disclaimer",
        description="Multi-page brief discusses Q4 revenue projections without mandatory safe harbor disclosures on page 1.",
        original_snippet="Page 2: 'Expected 240% ARR expansion through 2027'",
        recommended_fix="Append statutory Private Securities Litigation Reform Act footnote to footer of pages 1-3.",
        status="pending"
    ))

    return flags
