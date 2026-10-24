"""
API tests: image, audio and video checks are simulated, so results must be
labelled as such and must never be saved to history.
"""

import uuid

import pytest


def _upload(client, content_type, filename):
    return client.post(
        "/api/v1/verify/upload",
        data={
            "brand_id": f"test-brand-{uuid.uuid4().hex[:8]}",
            "content_type": content_type,
            "title": "Demo asset",
            "target_channel": "Social",
        },
        files={"file": (filename, b"fake bytes", "application/octet-stream")},
    )


def _newest_scan_id(client):
    rows = client.get("/api/v1/scans?limit=1").json()
    return rows[0]["scan_id"] if rows else None


@pytest.mark.parametrize(
    "content_type, filename",
    [("image", "ad.png"), ("audio", "ad.mp3"), ("video", "ad.mp4")],
)
def test_simulated_result_is_labelled(client, content_type, filename):
    response = _upload(client, content_type, filename)

    assert response.status_code == 200
    body = response.json()
    assert body["simulated"] is True
    assert body["saved"] is False
    assert body["overall_status"] == "simulated"
    assert body["compliance_score"] is None
    assert body["scan_id"] is None
    assert "demonstration" in body["notice"].lower()
    assert all(flag["title"].startswith("[SIMULATED]") for flag in body["flags"])


@pytest.mark.parametrize(
    "content_type, filename",
    [("image", "ad.png"), ("audio", "ad.mp3"), ("video", "ad.mp4")],
)
def test_simulated_result_is_not_saved(client, content_type, filename):
    before = _newest_scan_id(client)

    response = _upload(client, content_type, filename)

    assert response.status_code == 200
    assert _newest_scan_id(client) == before


def test_unknown_content_type_is_still_rejected(client):
    response = _upload(client, "hologram", "ad.xyz")
    assert response.status_code == 400
