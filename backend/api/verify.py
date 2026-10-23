"""
Pre-Flight Compliance Verification Endpoints
Supports scanning Text, Documents, Images, Audio, and Video assets.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
import uuid

from backend.models.scan import ScanRequest, ScanResult
from backend.services.text_verifier import verify_text_compliance
from backend.services.image_verifier import verify_image_compliance
from backend.services.doc_verifier import verify_document_compliance
from backend.services.audio_verifier import verify_audio_compliance
from backend.services.video_verifier import verify_video_compliance

router = APIRouter()

@router.post("/text", response_model=ScanResult)
async def verify_text_endpoint(payload: ScanRequest):
    """Scan ad copy or text against the brand rulebook and custom upload rules."""
    if not payload.raw_text:
        raise HTTPException(status_code=400, detail="raw_text field is required for text verification")

    diff_result = verify_text_compliance(payload.raw_text, payload.custom_rule)
    score = max(35, 100 - len(diff_result.flags) * 22)

    return ScanResult(
        scan_id=f"scan-{uuid.uuid4().hex[:8]}",
        brand_id=payload.brand_id,
        content_type="text",
        title=payload.title,
        target_channel=payload.target_channel,
        overall_status="warnings_detected" if diff_result.flags else "compliant",
        compliance_score=score,
        flags=diff_result.flags,
        diff=diff_result
    )

@router.post("/upload")
async def verify_file_upload(
    brand_id: str = Form(...),
    content_type: str = Form(...),  # document, image, audio, video
    title: str = Form(...),
    target_channel: str = Form(...),
    custom_rule: Optional[str] = Form(None),
    file: UploadFile = File(...)
):
    """Upload and verify binary creative assets (images, documents, audio stems, videos)."""
    flags = []

    if content_type == "image":
        flags = verify_image_compliance(file.filename, ["#ffffff", "#a1a1aa", "#121214"], custom_rule)
    elif content_type == "document":
        flags = verify_document_compliance(file.filename, custom_rule)
    elif content_type == "audio":
        flags = verify_audio_compliance(file.filename, custom_rule)
    elif content_type == "video":
        flags = verify_video_compliance(file.filename, custom_rule)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported content_type: {content_type}")

    score = max(50, 100 - len(flags) * 20)

    return {
        "scan_id": f"scan-{uuid.uuid4().hex[:8]}",
        "brand_id": brand_id,
        "content_type": content_type,
        "filename": file.filename,
        "title": title,
        "target_channel": target_channel,
        "overall_status": "warnings_detected" if flags else "compliant",
        "compliance_score": score,
        "flags": flags
    }
