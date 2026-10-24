"""
Nothing personal may be sent to the external AI service. Personal details are
masked first, and the real values are put back into the answer locally.
"""

import sys
import types

import pytest

from backend.config import settings
from backend.models.scan import ComplianceFlag, SeverityLevel
from backend.services.ai_explainer import explain_findings

TEXT = "Email jane@acme.com or call +91 98765 43210. Our engine is 10X faster."


def _flag():
    return ComplianceFlag(
        id="f",
        rule_citation="r",
        flag_type="t",
        severity=SeverityLevel.WARNING,
        title="Claim",
        description="Contact jane@acme.com about this",
        original_snippet="call +91 98765 43210",
        recommended_fix="Remove it",
    )


@pytest.fixture
def fake_groq(monkeypatch):
    """Replace the Groq client with one that records every request it gets."""
    calls = []

    class FakeGroq:
        def __init__(self, api_key=None, timeout=None):
            self.chat = types.SimpleNamespace(
                completions=types.SimpleNamespace(create=self._create)
            )

        def _create(self, **kwargs):
            calls.append(kwargs)
            message = types.SimpleNamespace(
                content="Please remove [EMAIL_1] and call [PHONE_1] only after review."
            )
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])

    monkeypatch.setitem(sys.modules, "groq", types.SimpleNamespace(Groq=FakeGroq))
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")
    return calls


def test_nothing_personal_is_sent_to_the_ai_service(fake_groq):
    explain_findings(TEXT, [_flag()])

    assert len(fake_groq) == 1
    sent = repr(fake_groq[0]["messages"])
    assert "jane@acme.com" not in sent
    assert "98765" not in sent
    assert "[EMAIL_1]" in sent
    assert "[PHONE_1]" in sent


def test_answer_gets_the_real_values_back(fake_groq):
    answer = explain_findings(TEXT, [_flag()])

    assert "jane@acme.com" in answer
    assert "+91 98765 43210" in answer
    assert "[EMAIL_1]" not in answer


def test_clean_scan_makes_no_ai_call(fake_groq):
    explain_findings(TEXT, [])
    assert fake_groq == []
