"""
Tests for the required-disclaimer check.
"""

from backend.services.disclaimer_check import check_required_disclaimers


def _ids(text):
    return [flag.id for flag in check_required_disclaimers(text)]


def test_forward_looking_language_without_disclaimer_is_flagged():
    assert _ids("We expect revenue to double next year.") == [
        "flag-disclaimer-forward-looking"
    ]


def test_forward_looking_language_with_disclaimer_is_clean():
    text = (
        "We expect revenue to double next year.\n"
        "This document contains forward-looking statements."
    )
    assert _ids(text) == []


def test_investment_returns_without_disclaimer_are_flagged():
    assert _ids("Our fund delivers annualized returns of 12%.") == [
        "flag-disclaimer-past-performance"
    ]


def test_investment_returns_with_disclaimer_are_clean():
    text = "Annual returns of 12%. Past performance is not a guarantee."
    assert _ids(text) == []


def test_text_with_no_trigger_language_is_clean():
    assert _ids("Our team ships a new feature every month.") == []


def test_both_rules_can_fire_together():
    text = "We expect growth. Investment returns of 9% are expected."
    assert _ids(text) == [
        "flag-disclaimer-forward-looking",
        "flag-disclaimer-past-performance",
    ]
