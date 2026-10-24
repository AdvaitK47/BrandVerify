"""
Document Compliance Verification Service
Extracts text from PDF/TXT files and runs compliance checks.
"""

from typing import List, Optional
import os
from backend.models.scan import ComplianceFlag, SeverityLevel
from backend.services.text_verifier import verify_text_compliance

# Optional: try importing pypdf or PyPDF2 for PDF text extraction
try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        PdfReader = None

def extract_document_text(file_path: str) -> str:
    """Extracts text from a PDF or text file."""
    text = ""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf" and PdfReader is not None:
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except Exception as e:
            raise RuntimeError(f"Failed to parse PDF: {str(e)}")
    else:
        # Fallback for plain text / markdown files
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception as e:
            raise RuntimeError(f"Failed to read document: {str(e)}")
            
    return text

def verify_document_compliance(
    file_path: str, 
    custom_rule: Optional[str] = None
) -> List[ComplianceFlag]:
    """
    Extracts text from uploaded documents (Whitepapers, Briefs) and evaluates them against compliance rules.
    """
    flags: List[ComplianceFlag] = []

    try:
        doc_text = extract_document_text(file_path)
    except Exception as e:
        flags.append(ComplianceFlag(
            id="flag-doc-error",
            rule_citation="Document Parser Engine",
            flag_type="system_warning",
            severity=SeverityLevel.WARNING,
            title="Document Text Extraction Failed",
            description=str(e),
            original_snippet=file_path,
            recommended_fix="Ensure the uploaded document is a valid, uncorrupted PDF or text file.",
            status="pending"
        ))
        return flags

    # Pass extracted document text into your core text verification engine
    if doc_text.strip():
        text_diff = verify_text_compliance(doc_text, custom_rule=custom_rule)
        for text_flag in text_diff.flags:
            text_flag.id = f"doc-{text_flag.id}"
            text_flag.description = f"[Detected in Document] {text_flag.description}"
            flags.append(text_flag)

    return flags