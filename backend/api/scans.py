from backend.db import SessionLocal, ScanRecord, AuditRecord

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from fastapi import Depends, HTTPException, Response
from sqlalchemy.orm import Session

from fastapi import Depends
from sqlalchemy.orm import Session
"""
Scan History and Review Endpoints

Read back saved compliance scans, record a human approve/reject decision on
a scan, and show the permanent audit log of those decisions.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.concurrency import run_in_threadpool

from backend import db
from backend.models.audit import AuditEntry, DecisionRequest
from backend.models.scan import ScanResult, ScanSummary

router = APIRouter()

PENDING = "pending_review"


@router.get("", response_model=List[ScanSummary])
async def list_scan_history(
    brand_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
):
    """List recent scans, newest first. Optionally filter by brand."""
    rows = await run_in_threadpool(db.list_scans, brand_id, limit)
    statuses = await run_in_threadpool(
        db.review_statuses, [row["scan_id"] for row in rows]
    )
    for row in rows:
        row["review_status"] = statuses.get(row["scan_id"], PENDING)
    return rows


@router.get("/{scan_id}", response_model=ScanResult)
async def get_scan_result(scan_id: str):
    """Retrieve the full saved result of one scan, with its review status."""
    result = await run_in_threadpool(db.get_scan, scan_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    statuses = await run_in_threadpool(db.review_statuses, [scan_id])
    result["review_status"] = statuses.get(scan_id, PENDING)
    return result


@router.post("/{scan_id}/decision", response_model=AuditEntry, status_code=201)
async def record_decision(scan_id: str, payload: DecisionRequest):
    """Approve or reject a scan. Every decision is added to the audit log.

    The reviewer name is typed in and is NOT verified until login is added.
    """
    scan = await run_in_threadpool(db.get_scan, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    reviewer = payload.reviewer.strip()
    comment = (payload.comment or "").strip() or None

    if not reviewer:
        raise HTTPException(status_code=422, detail="Reviewer name is required.")

    if payload.decision == "rejected" and not comment:
        raise HTTPException(
            status_code=422,
            detail="A comment is required when rejecting a scan.",
        )

    has_critical = any(
        flag.get("severity") == "critical" for flag in scan.get("flags", [])
    )
    overrode_critical = payload.decision == "approved" and has_critical
    if overrode_critical and not comment:
        raise HTTPException(
            status_code=422,
            detail=(
                "This scan has a critical finding. A comment explaining why "
                "it is approved anyway is required."
            ),
        )

    return await run_in_threadpool(
        db.add_audit_entry,
        scan_id,
        scan["brand_id"],
        payload.decision,
        reviewer,
        comment,
        overrode_critical,
    )


@router.get("/{scan_id}/audit", response_model=List[AuditEntry])
async def get_audit_log(scan_id: str):
    """Every decision made on this scan, oldest first."""
    scan = await run_in_threadpool(db.get_scan, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return await run_in_threadpool(db.list_audit, scan_id)




@router.get("/{scan_id}/report.pdf")
def download_scan_pdf_report(scan_id: str, db: Session = Depends(get_db)):
    from backend.services.pdf_report import generate_scan_pdf_report
    from backend.models.audit import AuditRecord

    scan = db.query(ScanResult).filter(ScanResult.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    audit_records = db.query(AuditRecord).filter(AuditRecord.scan_id == scan_id).order_by(AuditRecord.timestamp.asc()).all()
    pdf_bytes = generate_scan_pdf_report(scan, audit_records)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=audit_report_{scan_id}.pdf"}
    )