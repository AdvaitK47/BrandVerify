"""
Tests for the shared overall-status rule.
"""

from backend.api.verify import determine_overall_status
from backend.models.scan import ComplianceFlag, SeverityLevel


def _flag(severity):
    return ComplianceFlag(
        id="f", rule_citation="r", flag_type="t", severity=severity,
        title="t", description="d", original_snippet="s", recommended_fix="x",
    )


def test_no_flags_is_compliant():
    assert determine_overall_status([]) == "compliant"


def test_info_only_is_compliant():
    assert determine_overall_status([_flag(SeverityLevel.INFO)]) == "compliant"


def test_warning_is_warnings_detected():
    flags = [_flag(SeverityLevel.INFO), _flag(SeverityLevel.WARNING)]
    assert determine_overall_status(flags) == "warnings_detected"


def test_critical_is_warnings_detected():
    assert determine_overall_status([_flag(SeverityLevel.CRITICAL)]) == "warnings_detected"


def test_upload_with_info_only_result_is_compliant(client):
    # The audio checker is still a mock that returns one INFO flag.
    # This test documents today's behavior and should be revisited when
    # the real audio verifier replaces the mock.
    response = client.post(
        "/api/v1/verify/upload",
        data={
            "brand_id": "test-brand",
            "content_type": "audio",
            "title": "Podcast read",
            "target_channel": "Podcast",
        },
        files={"file": ("read.mp3", b"fake audio bytes", "audio/mpeg")},
    )
    assert response.status_code == 200
    assert response.json()["overall_status"] == "compliant"
