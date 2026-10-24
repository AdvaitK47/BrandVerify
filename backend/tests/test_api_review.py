"""
API tests: approve/reject decisions and the permanent audit log.
"""

import uuid

import pytest

from backend import db
from backend.db import AuditLogError, AuditRecord

# Warnings only (no critical flag).
PLAIN_TEXT = "Our engine is guaranteed to be 10X faster."
# "zero downtime" is a critical finding under the default rules.
CRITICAL_TEXT = "We promise zero downtime for every customer."


def _scan(client, text=PLAIN_TEXT, brand_id=None):
    response = client.post(
        "/api/v1/verify/text",
        json={
            "brand_id": brand_id or f"test-brand-{uuid.uuid4().hex[:8]}",
            "content_type": "text",
            "title": "Headline",
            "target_channel": "Web",
            "raw_text": text,
        },
    )
    assert response.status_code == 200
    return response.json()


def _decide(client, scan_id, decision, reviewer="Priya", comment=None):
    return client.post(
        f"/api/v1/scans/{scan_id}/decision",
        json={"decision": decision, "reviewer": reviewer, "comment": comment},
    )


def test_new_scan_starts_as_pending_review(client):
    scan = _scan(client)
    assert scan["review_status"] == "pending_review"

    saved = client.get(f"/api/v1/scans/{scan['scan_id']}").json()
    assert saved["review_status"] == "pending_review"


def test_approving_a_scan_without_critical_flags_needs_no_comment(client):
    scan = _scan(client)
    response = _decide(client, scan["scan_id"], "approved")

    assert response.status_code == 201
    entry = response.json()
    assert entry["action"] == "approved"
    assert entry["reviewer"] == "Priya"
    assert entry["overrode_critical"] is False

    saved = client.get(f"/api/v1/scans/{scan['scan_id']}").json()
    assert saved["review_status"] == "approved"


def test_rejecting_requires_a_comment(client):
    scan = _scan(client)

    assert _decide(client, scan["scan_id"], "rejected").status_code == 422
    assert _decide(client, scan["scan_id"], "rejected", comment="   ").status_code == 422

    response = _decide(client, scan["scan_id"], "rejected", comment="Claims are unproven")
    assert response.status_code == 201

    saved = client.get(f"/api/v1/scans/{scan['scan_id']}").json()
    assert saved["review_status"] == "rejected"


def test_approving_a_critical_scan_needs_an_override_comment(client):
    scan = _scan(client, CRITICAL_TEXT)
    assert any(flag["severity"] == "critical" for flag in scan["flags"])

    assert _decide(client, scan["scan_id"], "approved").status_code == 422

    response = _decide(
        client, scan["scan_id"], "approved", comment="Legal confirmed our SLA wording"
    )
    assert response.status_code == 201
    assert response.json()["overrode_critical"] is True


def test_audit_log_keeps_every_decision_in_order(client):
    scan = _scan(client)
    _decide(client, scan["scan_id"], "rejected", reviewer="Priya", comment="Needs evidence")
    _decide(client, scan["scan_id"], "approved", reviewer="Arun", comment="Evidence added")

    audit = client.get(f"/api/v1/scans/{scan['scan_id']}/audit").json()

    assert [entry["action"] for entry in audit] == ["rejected", "approved"]
    assert [entry["reviewer"] for entry in audit] == ["Priya", "Arun"]
    assert audit[0]["id"] < audit[1]["id"]

    # The latest decision is the current status.
    saved = client.get(f"/api/v1/scans/{scan['scan_id']}").json()
    assert saved["review_status"] == "approved"


def test_scan_history_shows_review_status(client):
    brand = f"test-brand-{uuid.uuid4().hex[:8]}"
    scan = _scan(client, brand_id=brand)
    _decide(client, scan["scan_id"], "approved")

    rows = client.get(f"/api/v1/scans?brand_id={brand}&limit=5").json()

    assert [row["scan_id"] for row in rows] == [scan["scan_id"]]
    assert rows[0]["review_status"] == "approved"


def test_unknown_scan_returns_404(client):
    assert _decide(client, "scan-doesnotexist", "approved").status_code == 404
    assert client.get("/api/v1/scans/scan-doesnotexist/audit").status_code == 404


def test_blank_reviewer_is_rejected(client):
    scan = _scan(client)
    assert _decide(client, scan["scan_id"], "approved", reviewer="   ").status_code == 422


def test_unknown_decision_value_is_rejected(client):
    scan = _scan(client)
    assert _decide(client, scan["scan_id"], "maybe").status_code == 422


def test_audit_entries_cannot_be_changed_or_deleted(client):
    scan = _scan(client)
    entry = _decide(client, scan["scan_id"], "approved", comment="Looks fine").json()

    with pytest.raises(AuditLogError):
        with db.SessionLocal() as session:
            session.get(AuditRecord, entry["id"]).comment = "edited"
            session.commit()

    with pytest.raises(AuditLogError):
        with db.SessionLocal() as session:
            session.delete(session.get(AuditRecord, entry["id"]))
            session.commit()

    audit = client.get(f"/api/v1/scans/{scan['scan_id']}/audit").json()
    assert len(audit) == 1
    assert audit[0]["comment"] == "Looks fine"
