"""
Pre-Flight Scan & Compliance Review Data Models
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class SeverityLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class ComplianceFlag(BaseModel):
    id: str
    rule_citation: str
    flag_type: str  # superlative, missing_disclaimer, color_mismatch, margin_violation, audio_loudness
    severity: SeverityLevel
    title: str
    description: str
    original_snippet: str
    recommended_fix: str
    status: str = "pending"  # pending, accepted, dismissed

class ScanDiffItem(BaseModel):
    original_text: str
    recommended_text: str
    flags: List[ComplianceFlag] = Field(default_factory=list)

class ScanRequest(BaseModel):
    brand_id: str
    content_type: str  # text, document, image, audio, video
    title: str
    target_channel: str
    custom_rule: Optional[str] = None
    raw_text: Optional[str] = None
    file_url: Optional[str] = None

class ScanResult(BaseModel):
    scan_id: str
    brand_id: str
    content_type: str
    title: str
    target_channel: str
    overall_status: str  # compliant, non_compliant, warnings_detected
    compliance_score: int = Field(..., ge=0, le=100)
    flags: List[ComplianceFlag] = Field(default_factory=list)
    diff: Optional[ScanDiffItem] = None
    scanned_at: datetime = Field(default_factory=datetime.utcnow)
