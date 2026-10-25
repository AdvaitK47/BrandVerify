
"""POST /api/v1/verify/text  - used by the Text tab in brand.html."""
 
import uuid
 
from fastapi import APIRouter, HTTPException
 
from backend.models.scan import ScanRequest, ScanResult
from backend.services.text_verifier import verify_text_compliance
 
router = APIRouter(prefix="/api/v1/verify", tags=["Text Compliance"])
 
DEDUCTIONS = {"critical": 30, "high": 20, "warning": 15, "medium": 15, "low": 5, "info": 0}
 
 
def _severity(flag) -> str:
    sev = getattr(flag.severity, "value", flag.severity)
    return str(sev).lower()
 
 
@router.post("/text", response_model=ScanResult)
def verify_text(req: ScanRequest):
    """Sync endpoint on purpose: FastAPI runs it in a worker thread, so the AI call can't block the server."""
    text = (req.raw_text or "").strip()
    if not text:
        raise HTTPException(422, "raw_text is required.")
 
    diff = verify_text_compliance(text, custom_rule=req.custom_rule)
    flags = diff.flags
 
    score = max(0, 100 - sum(DEDUCTIONS.get(_severity(f), 0) for f in flags))
    severities = {_severity(f) for f in flags}
    if "critical" in severities:
        status = "non_compliant"
    elif flags:
        status = "warnings_detected"
    else:
        status = "compliant"
 
    # The AI explanation is optional: a missing groq package or API key must not break the scan.
    try:
        from backend.services.ai_explainer import explain_findings
        explanation = explain_findings(text, flags)
    except Exception:
        explanation = "AI explanation is unavailable. The rule-based findings are still shown."
 
    return ScanResult(
        scan_id=f"scan-{uuid.uuid4().hex[:8]}",
        brand_id=req.brand_id,
        content_type=req.content_type,
        title=req.title,
        target_channel=req.target_channel,
        overall_status=status,
        compliance_score=score,
        flags=flags,
        ai_explanation=explanation,
        diff=diff,
    )
 
