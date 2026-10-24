"""
API tests: the brand_id on a request decides which rules are applied.
"""

import io
import uuid

import pytest


def _other_brand():
    """A brand id with no rule file, so it gets the default rules."""
    return f"test-brand-{uuid.uuid4().hex[:8]}"


def _text_scan(client, brand_id, raw_text):
    return client.post(
        "/api/v1/verify/text",
        json={
            "brand_id": brand_id,
            "content_type": "text",
            "title": "Headline",
            "target_channel": "Web",
            "raw_text": raw_text,
        },
    )


def _doc_scan(client, brand_id, *paragraphs):
    docx = pytest.importorskip("docx")
    document = docx.Document()
    for text in paragraphs:
        document.add_paragraph(text)
    buffer = io.BytesIO()
    document.save(buffer)

    return client.post(
        "/api/v1/verify/upload",
        data={
            "brand_id": brand_id,
            "content_type": "document",
            "title": "Product sheet",
            "target_channel": "Web",
        },
        files={"file": ("sheet.docx", buffer.getvalue(), "application/octet-stream")},
    )


def test_text_scan_uses_the_brand_rules(client):
    text = "Our fund is risk-free."

    apex = _text_scan(client, "apex-fin", text).json()
    assert apex["overall_status"] == "warnings_detected"
    assert apex["compliance_score"] == 70  # one critical flag: 100 - 30

    other = _text_scan(client, _other_brand(), text).json()
    assert other["overall_status"] == "compliant"
    assert other["compliance_score"] == 100


def test_document_scan_flags_missing_brand_disclaimer(client):
    response = _doc_scan(client, "pulse-health", "Our formula supports immune health every day.")

    assert response.status_code == 200
    body = response.json()
    assert body["compliance_score"] == 85  # one warning: 100 - 15
    assert [flag["id"] for flag in body["flags"]] == ["flag-disclaimer-dietary-supplement"]


def test_document_scan_accepts_brand_disclaimer_when_present(client):
    response = _doc_scan(
        client,
        "pulse-health",
        "Our formula supports immune health every day.",
        "These statements have not been evaluated by the Food and Drug Administration.",
    )

    body = response.json()
    assert body["overall_status"] == "compliant"
    assert body["compliance_score"] == 100


def test_other_brands_are_not_asked_for_the_supplement_disclaimer(client):
    response = _doc_scan(client, _other_brand(), "Our formula supports immune health every day.")

    body = response.json()
    assert body["overall_status"] == "compliant"
    assert body["compliance_score"] == 100
