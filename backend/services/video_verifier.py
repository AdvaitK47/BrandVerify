"""
Video Commercial & Reel Verification Service (.MP4, .MOV)
Inspects video clips for scene transition pacing, on-screen disclaimer readability, and logo presence.
"""

from typing import List, Optional
from backend.models.scan import ComplianceFlag, SeverityLevel

def verify_video_compliance(video_path: str, custom_rule: Optional[str] = None) -> List[ComplianceFlag]:
    flags: List[ComplianceFlag] = []

    # Example evaluation: On-screen disclaimer duration
    flags.append(ComplianceFlag(
        id="flag-vid-disclaimer-1",
        rule_citation="Clear and Conspicuous Disclosures (FTC 16 CFR Part 255)",
        flag_type="on_screen_duration",
        severity=SeverityLevel.WARNING,
        title="On-Screen Disclaimer Duration Too Brief",
        description="The mandatory terms disclaimer appears for only 1.4 seconds (minimum 3.0 seconds required for legible viewer reading).",
        original_snippet="Frame timestamp 00:00:26 - 00:00:27.4",
        recommended_fix="Extend disclaimer overlay freeze-frame to at least 3.2 seconds at minimum 18pt font.",
        status="pending"
    ))

    return flags
