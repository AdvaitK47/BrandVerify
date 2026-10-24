"""
The AI explanation is a slow network call. It must run in a worker thread,
never directly on the server's event loop, or one slow call would freeze
every other request.
"""

import asyncio
import io
import uuid

import pytest


def _make_probe(seen):
    """A fake explainer that records where it was called from."""

    def probe(text, flags):
        try:
            asyncio.get_running_loop()
            seen.append("event_loop")
        except RuntimeError:
            seen.append("worker_thread")
        return "TEST EXPLANATION"

    return probe


def test_text_scan_runs_ai_call_in_worker_thread(client, monkeypatch):
    from backend.api import verify

    seen = []
    monkeypatch.setattr(verify, "explain_findings", _make_probe(seen))

    response = client.post(
        "/api/v1/verify/text",
        json={
            "brand_id": f"test-brand-{uuid.uuid4().hex[:8]}",
            "content_type": "text",
            "title": "Headline",
            "target_channel": "Web",
            "raw_text": "Our engine is guaranteed to be 10X faster.",
        },
    )

    assert response.status_code == 200
    assert seen == ["worker_thread"]


def test_document_scan_runs_ai_call_in_worker_thread(client, monkeypatch):
    docx = pytest.importorskip("docx")
    from backend.api import verify

    seen = []
    monkeypatch.setattr(verify, "explain_findings", _make_probe(seen))

    document = docx.Document()
    document.add_paragraph("Our engine is guaranteed to be 10X faster.")
    buffer = io.BytesIO()
    document.save(buffer)

    response = client.post(
        "/api/v1/verify/upload",
        data={
            "brand_id": f"test-brand-{uuid.uuid4().hex[:8]}",
            "content_type": "document",
            "title": "Deck",
            "target_channel": "Investor Brief",
        },
        files={"file": ("deck.docx", buffer.getvalue(), "application/octet-stream")},
    )

    assert response.status_code == 200
    assert seen == ["worker_thread"]
