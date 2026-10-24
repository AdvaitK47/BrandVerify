"""
API tests: required-disclaimer checks on uploaded .docx documents.
"""

import io
import uuid

import pytest


def _docx_bytes(paragraphs, footer=None):
    docx = pytest.importorskip("docx")
    document = docx.Document()
    for text in paragraphs:
        document.add_paragraph(text)
    if footer:
        document.sections[0].footer.paragraphs[0].text = footer
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _upload(client, filename, data):
    return client.post(
        "/api/v1/verify/upload",
        data={
            "brand_id": f"test-brand-{uuid.uuid4().hex[:8]}",
            "content_type": "document",
            "title": "Investor brief",
            "target_channel": "Investor Brief",
        },
        files={"file": (filename, data, "application/octet-stream")},
    )


def test_missing_disclaimer_is_flagged(client):
    data = _docx_bytes(["We expect revenue to double next year."])
    response = _upload(client, "brief.docx", data)

    assert response.status_code == 200
    body = response.json()
    assert body["overall_status"] == "warnings_detected"
    assert body["compliance_score"] == 85  # 100 - 15
    flag_types = [flag["flag_type"] for flag in body["flags"]]
    assert "missing_disclaimer" in flag_types


def test_disclaimer_present_in_body_is_compliant(client):
    data = _docx_bytes(
        [
            "We expect revenue to double next year.",
            "This brief contains forward-looking statements.",
        ]
    )
    response = _upload(client, "brief.docx", data)

    assert response.status_code == 200
    body = response.json()
    assert body["overall_status"] == "compliant"
    assert body["compliance_score"] == 100


def test_disclaimer_in_footer_counts(client):
    data = _docx_bytes(
        ["We expect revenue to double next year."],
        footer="Forward-looking statements disclaimer applies.",
    )
    response = _upload(client, "brief.docx", data)

    assert response.status_code == 200
    body = response.json()
    assert body["overall_status"] == "compliant"
    assert body["compliance_score"] == 100
