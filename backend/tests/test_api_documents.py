"""
API tests for document upload scanning (.docx; .pdf when PyMuPDF is installed).
"""

import io
import uuid

import pytest


def _docx_bytes(*paragraphs):
    docx = pytest.importorskip("docx")
    document = docx.Document()
    for text in paragraphs:
        document.add_paragraph(text)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _upload(client, filename, data, brand_id=None, custom_rule=None):
    form = {
        "brand_id": brand_id or f"test-brand-{uuid.uuid4().hex[:8]}",
        "content_type": "document",
        "title": "Pitch deck",
        "target_channel": "Investor Brief",
    }
    if custom_rule:
        form["custom_rule"] = custom_rule
    return client.post(
        "/api/v1/verify/upload",
        data=form,
        files={"file": (filename, data, "application/octet-stream")},
    )


def test_docx_with_risky_claims_is_flagged_and_saved(client):
    data = _docx_bytes("Our engine is guaranteed to be 10X faster.")
    response = _upload(client, "deck.docx", data)

    assert response.status_code == 200
    body = response.json()
    assert body["content_type"] == "document"
    assert body["overall_status"] == "warnings_detected"
    assert body["compliance_score"] == 70  # 100 - 15 - 15
    assert body["ai_explanation"] == "TEST EXPLANATION"
    assert body["diff"] is None

    saved = client.get(f"/api/v1/scans/{body['scan_id']}")
    assert saved.status_code == 200
    assert saved.json()["content_type"] == "document"


def test_clean_docx_is_compliant(client):
    data = _docx_bytes("Our team ships a new feature every month.")
    response = _upload(client, "clean.docx", data)

    assert response.status_code == 200
    body = response.json()
    assert body["overall_status"] == "compliant"
    assert body["compliance_score"] == 100


def test_unsupported_document_type_is_rejected(client):
    response = _upload(client, "notes.txt", b"hello")
    assert response.status_code == 400


def test_corrupt_docx_returns_422(client):
    response = _upload(client, "broken.docx", b"not a real word file")
    assert response.status_code == 422


def test_docx_without_text_returns_422(client):
    response = _upload(client, "empty.docx", _docx_bytes())
    assert response.status_code == 422


def test_oversized_upload_returns_413(client, monkeypatch):
    from backend.config import settings

    monkeypatch.setattr(settings, "MAX_UPLOAD_MB", 0)
    response = _upload(client, "big.docx", b"x")
    assert response.status_code == 413
