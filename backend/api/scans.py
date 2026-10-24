"""
Scan History Endpoints
Read back previously saved compliance scans.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.concurrency import run_in_threadpool

from backend import db
from backend.models.scan import ScanResult, ScanSummary

router = APIRouter()


@router.get("", response_model=List[ScanSummary])
async def list_scan_history(
    brand_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
):
    """List recent scans, newest first. Optionally filter by brand."""
    return await run_in_threadpool(db.list_scans, brand_id, limit)


@router.get("/{scan_id}", response_model=ScanResult)
async def get_scan_result(scan_id: str):
    """Retrieve the full saved result of one scan."""
    result = await run_in_threadpool(db.get_scan, scan_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return result
