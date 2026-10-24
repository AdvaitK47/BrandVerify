"""
API tests for text scanning and scan history.
"""

import uuid


def _new_brand_id() -> str:
    # A unique brand per test, so tests never see each other's scans.
    return f"test-brand-{uuid.uuid4().hex[:8]}"


def _scan(client, brand_id, text="We are guaranteed to be 10X faster.", title="Test scan"):
    return client.post(
        "/api/v1/verify/text",
        json={
            "brand_id": brand_id,
            "content_type": "text",
            "title": title,
            "target_channel": "Social Media",
            "raw_text": text,
        },
    )


def test_uses_throwaway_database():
    """Safety check: tests must never use the real brandverify.db."""
    from backend import db

    assert "bv_test_" in str(db.engine.url)


def test_scan_is_saved_and_listed(client):
    brand = _new_brand_id()
    response = _scan(client, brand)

    assert response.status_code == 200
    scan_id = response.json()["scan_id"]

    history = client.get("/api/v1/scans", params={"brand_id": brand})
    assert history.status_code == 200

    items = history.json()
    assert len(items) == 1
    assert items[0]["scan_id"] == scan_id
    assert items[0]["compliance_score"] == 70  # 100 - 15 - 15


def test_get_scan_by_id_returns_full_result(client):
    brand = _new_brand_id()
    scan_id = _scan(client, brand, title="Full result check").json()["scan_id"]

    response = client.get(f"/api/v1/scans/{scan_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == "Full result check"
    assert len(data["flags"]) == 2
    assert data["ai_explanation"] == "TEST EXPLANATION"
    assert "[REVIEW:" in data["diff"]["recommended_text"]


def test_unknown_scan_returns_404(client):
    response = client.get("/api/v1/scans/scan-does-not-exist")
    assert response.status_code == 404


def test_history_can_be_filtered_by_brand(client):
    brand_a = _new_brand_id()
    brand_b = _new_brand_id()
    _scan(client, brand_a)
    _scan(client, brand_b)

    items = client.get("/api/v1/scans", params={"brand_id": brand_a}).json()
    assert len(items) == 1
    assert items[0]["brand_id"] == brand_a


def test_empty_text_is_rejected(client):
    response = _scan(client, _new_brand_id(), text="   ")
    assert response.status_code == 400


def test_limit_must_be_at_least_one(client):
    response = client.get("/api/v1/scans", params={"limit": 0})
    assert response.status_code == 422
