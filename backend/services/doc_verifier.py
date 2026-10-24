"""
Document Verification Service (.PDF, .DOCX)

Extracts the document's text and runs the same claim rules used for text
scans, so one rule set powers both, then checks for required disclaimers.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

from backend.models.scan import ComplianceFlag
from backend.services.brand_rules import load_rules
from backend.services.disclaimer_check import check_required_disclaimers
from backend.services.doc_extractor import DocumentError, extract_document
from backend.services.text_verifier import verify_text_compliance


@dataclass
class DocumentScan:
    flags: List[ComplianceFlag]
    text: str
    page_count: int


def verify_document(
    file_path: Union[str, Path],
    custom_rule: Optional[str] = None,
    filename: Optional[str] = None,
    brand_id: Optional[str] = None,
) -> DocumentScan:
    """Read a document and scan its text. Raises DocumentError if unreadable."""
    extracted = extract_document(file_path, filename)

    if not extracted.has_text:
        raise DocumentError(
            "No readable text was found. This may be a scanned document; "
            "scanned documents (OCR) are not supported yet."
        )

    rules = load_rules(brand_id)
    diff = verify_text_compliance(extracted.text, custom_rule, rules)
    flags = diff.flags + check_required_disclaimers(extracted.text, rules)
    return DocumentScan(
        flags=flags,
        text=extracted.text,
        page_count=extracted.page_count,
    )


def verify_document_compliance(
    file_path: Union[str, Path],
    custom_rule: Optional[str] = None,
    filename: Optional[str] = None,
) -> List[ComplianceFlag]:
    """Flags only. Kept so the services package API stays the same."""
    return verify_document(file_path, custom_rule, filename).flags
