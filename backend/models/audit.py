"""
Review decision and audit log data models.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class DecisionRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    reviewer: str = Field(..., min_length=1, max_length=100)
    comment: Optional[str] = Field(None, max_length=2000)


class AuditEntry(BaseModel):
    id: int
    scan_id: str
    brand_id: str
    action: str  # approved, rejected
    reviewer: str
    comment: Optional[str] = None
    overrode_critical: bool = False
    created_at: datetime
