"""
Tests for PII masking (text that leaves the server is masked first).
"""

import pytest

from backend.services.pii_masker import PiiMasker


def test_email_is_masked_and_restored():
    masker = PiiMasker()
    masked = masker.mask("Write to jane.doe@acme-corp.com today.")

    assert masked == "Write to [EMAIL_1] today."
    assert masker.unmask(masked) == "Write to jane.doe@acme-corp.com today."


@pytest.mark.parametrize(
    "number",
    ["+91 98765 43210", "(555) 123-4567", "555-123-4567", "9876543210"],
)
def test_phone_numbers_in_common_formats_are_masked(number):
    masker = PiiMasker()
    assert masker.mask(f"Call {number} now") == "Call [PHONE_1] now"


@pytest.mark.parametrize(
    "case",
    [
        ("CARD", "4111 1111 1111 1111"),
        ("CARD", "4111-1111-1111-1112"),
        ("ID", "123-45-6789"),
        ("ID", "ABCDE1234F"),
        ("ID", "1234 5678 9012"),
    ],
)
def test_card_and_id_numbers_are_masked(case):
    kind, value = case
    masker = PiiMasker()
    assert masker.mask(f"Ref {value} here") == f"Ref [{kind}_1] here"


@pytest.mark.parametrize(
    "text",
    [
        "Our engine is 10X faster.",
        "It has 99.9% uptime.",
        "Updated on 2026-10-24.",
        "Revenue grew 120% to $4,500,000 in Q3 2025.",
    ],
)
def test_ordinary_marketing_numbers_are_left_alone(text):
    assert PiiMasker().mask(text) == text


def test_same_value_gets_the_same_placeholder():
    masker = PiiMasker()
    masked = masker.mask("a@x.io and again a@x.io plus b@x.io")
    assert masked == "[EMAIL_1] and again [EMAIL_1] plus [EMAIL_2]"


def test_round_trip_restores_everything():
    original = (
        "Jane (jane@acme.com, +91 98765 43210, card 4111 1111 1111 1111, "
        "SSN 123-45-6789, PAN ABCDE1234F) said 10X faster."
    )
    masker = PiiMasker()
    masked = masker.mask(original)

    assert "jane@acme.com" not in masked
    assert "98765" not in masked
    assert "4111" not in masked
    assert masker.unmask(masked) == original


def test_unknown_placeholder_is_left_alone():
    masker = PiiMasker()
    masker.mask("a@x.io")
    assert masker.unmask("See [EMAIL_1] and [EMAIL_9]") == "See a@x.io and [EMAIL_9]"
