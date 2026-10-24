
"""
Pre-Flight Compliance Verification Endpoints.

Text findings use heuristic checks and uploaded brand rulebooks.
AI explains findings but does not determine the compliance score.
"""

from typing import Optional
import uuid

import pymupdf
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.models.scan import ScanRequest, ScanResult
from backend.services.text_verifier import verify_text_compliance
from backend.services.ai_explainer import explain_findings
from backend.services.image_verifier import verify_image_compliance
from backend.services.doc_verifier import verify_document_compliance
from backend.services.audio_verifier import verify_audio_compliance
from backend.services.video_verifier import verify_video_compliance

router = APIRouter()

MAX_PDF_SIZE = 10 * 1024 * 1024
MAX_PDF_PAGES = 200
MAX_RULEBOOK_CHARACTERS = 100_000

# Temporary in-memory storage. Uploaded rulebooks are lost when the
# backend process restarts.
BRAND_RULEBOOKS = {}



def calculate_compliance_score(flags) -> int:
    """Calculate a preliminary score without double-counting the same claim."""

    deductions = {
        "critical": 30,
        "high": 20,
        "warning": 10,
        "medium": 10,
        "low": 5,
        "info": 0,
        "informational": 0,
    }

    total_deduction = 0
    seen_claims = set()

    for flag in flags:
        severity = getattr(flag, "severity", "info")
        severity = getattr(severity, "value", severity)
        severity = str(severity).lower()

        snippet = getattr(flag, "original_snippet", None)

        # Avoid counting the same phrase twice, even if two checks flag it.
        if snippet:
            key = snippet.casefold()
            if key in seen_claims:
                continue
            seen_claims.add(key)

        total_deduction += deductions.get(severity, 0)

    return max(0, min(100, 100 - total_deduction))

def has_warnings(flags) -> bool:
    """Return True if any finding is not informational."""

    return any(
        str(getattr(flag.severity, "value", flag.severity)).lower()
        not in ("info", "informational")
        for flag in flags
    )


@router.post("/text", response_model=ScanResult)
async def verify_text_endpoint(payload: ScanRequest):
    """Scan text against general checks and the selected brand rulebook."""

    if not payload.raw_text or not payload.raw_text.strip():
        raise HTTPException(
            status_code=400,
            detail="raw_text field is required for text verification",
        )

    brand_rules = BRAND_RULEBOOKS.get(payload.brand_id, {}).get("text", "")

    diff_result = verify_text_compliance(
        payload.raw_text,
        custom_rule=payload.custom_rule,
        brand_rules_text=brand_rules,
    )

    score = calculate_compliance_score(diff_result.flags)

    ai_explanation = explain_findings(
        payload.raw_text,
        diff_result.flags,
    )

    return ScanResult(
        scan_id=f"scan-{uuid.uuid4().hex[:8]}",
        brand_id=payload.brand_id,
        content_type="text",
        title=payload.title,
        target_channel=payload.target_channel,
        overall_status=(
            "warnings_detected" if has_warnings(diff_result.flags)
            else "compliant"
        ),
        compliance_score=score,
        flags=diff_result.flags,
        ai_explanation=ai_explanation,
        diff=diff_result,
    )


@router.post("/rulebook")
async def upload_rulebook(
    brand_id: str = Form(...),
    file: UploadFile = File(...),
):
    """Extract selectable text from a PDF and store it for a brand."""

    if not brand_id.strip():
        raise HTTPException(status_code=400, detail="brand_id is required")

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF rulebook.",
        )

    contents = await file.read()

    if not contents:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    if len(contents) > MAX_PDF_SIZE:
        raise HTTPException(
            status_code=413,
            detail="PDF exceeds the 10 MB upload limit.",
        )

    try:
        with pymupdf.open(stream=contents, filetype="pdf") as document:
            if document.is_encrypted:
                raise HTTPException(
                    status_code=400,
                    detail="Password-protected PDFs are not supported.",
                )

            if len(document) > MAX_PDF_PAGES:
                raise HTTPException(
                    status_code=400,
                    detail="PDF exceeds the 200-page limit.",
                )

            extracted_text = "\n".join(
                page.get_text() for page in document
            ).strip()

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Could not read this PDF. Please check that it is a valid PDF.",
        ) from exc

    if not extracted_text:
        raise HTTPException(
            status_code=400,
            detail=(
                "No selectable text was found. "
                "Please upload a text-based PDF rather than a scanned image."
            ),
        )

    stored_text = extracted_text[:MAX_RULEBOOK_CHARACTERS]

    BRAND_RULEBOOKS[brand_id] = {
        "filename": file.filename,
        "text": stored_text,
        "character_count": len(stored_text),
    }

    return {
        "message": "PDF text extracted and stored for this brand.",
        "brand_id": brand_id,
        "filename": file.filename,
        "character_count": len(stored_text),
        "preview": stored_text[:1000],
        "note": (
            "The extracted text will be used by the text checker for "
            "supported prohibited-phrase and disclaimer checks. "
            "This does not interpret every possible rule in the PDF."
        ),
    }


@router.post("/upload")
async def verify_file_upload(
    brand_id: str = Form(...),
    content_type: str = Form(...),
    title: str = Form(...),
    target_channel: str = Form(...),
    custom_rule: Optional[str] = Form(None),
    file: UploadFile = File(...),
):
    """Run the existing checks for uploaded creative assets."""

    if content_type == "image":
        flags = verify_image_compliance(
            file.filename,
            ["#ffffff", "#a1a1aa", "#121214"],
            custom_rule,
        )
    elif content_type == "document":
        flags = verify_document_compliance(file.filename, custom_rule)
    elif content_type == "audio":
        flags = verify_audio_compliance(file.filename, custom_rule)
    elif content_type == "video":
        flags = verify_video_compliance(file.filename, custom_rule)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported content_type: {content_type}",
        )

    return {
        "scan_id": f"scan-{uuid.uuid4().hex[:8]}",
        "brand_id": brand_id,
        "content_type": content_type,
        "filename": file.filename,
        "title": title,
        "target_channel": target_channel,
        "overall_status": (
            "warnings_detected" if has_warnings(flags) else "compliant"
        ),
        "compliance_score": calculate_compliance_score(flags),
        "flags": flags,
    }
