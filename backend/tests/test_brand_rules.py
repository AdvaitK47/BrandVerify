"""
Tests for per-brand rule files (backend/rules/*.json) and the loader.
"""

import json

import pytest

from backend.services import brand_rules
from backend.services.brand_rules import RuleFileError, load_all_rule_files, load_rules
from backend.services.disclaimer_check import check_required_disclaimers
from backend.services.text_verifier import verify_text_compliance

EXPECTED_BRANDS = {"default", "acme-tech", "luxe-fashion", "apex-fin", "pulse-health"}


def _titles(brand, text):
    return [f.title for f in verify_text_compliance(text, None, load_rules(brand)).flags]


def test_every_shipped_rule_file_is_valid():
    # Parsing every file also compiles every pattern, so a typo fails here.
    rule_sets = load_all_rule_files()
    assert EXPECTED_BRANDS <= set(rule_sets)


def test_unknown_brand_uses_default_rules():
    assert load_rules("test-brand-123").brand_id == "default"
    assert load_rules(None).brand_id == "default"
    assert load_rules("").brand_id == "default"


def test_brand_id_cannot_escape_the_rules_folder():
    for bad in ["../../etc/passwd", "..\\..\\secret", "apex-fin/../../x", "/etc/passwd"]:
        assert load_rules(bad).brand_id == "default"


def test_brand_lookup_ignores_case():
    assert load_rules("Apex-Fin").brand_id == "apex-fin"


def test_same_text_gets_different_flags_per_brand():
    text = "Our fund is risk-free and clinically proven, with guaranteed returns."

    assert _titles("default", text) == [
        "Guarantee language may need supporting terms and evidence"
    ]
    assert _titles("apex-fin", text) == [
        "Absolute risk claim needs substantiation",
        "Guaranteed return language is high risk",
    ]
    assert _titles("pulse-health", text) == [
        "Clinical evidence claim needs substantiation"
    ]


def test_severity_comes_from_the_rule_file():
    diff = verify_text_compliance("Our fund is risk-free.", None, load_rules("apex-fin"))
    assert [f.severity.value for f in diff.flags] == ["critical"]


def test_disclaimer_rules_follow_the_brand():
    text = "We expect revenue to double next year."

    assert check_required_disclaimers(text, load_rules("luxe-fashion")) == []
    assert [f.id for f in check_required_disclaimers(text, load_rules("apex-fin"))] == [
        "flag-disclaimer-forward-looking"
    ]


@pytest.fixture
def rules_dir(tmp_path, monkeypatch):
    """Point the loader at an empty temporary folder for this test only."""
    monkeypatch.setattr(brand_rules, "RULES_DIR", tmp_path)
    return tmp_path


@pytest.mark.parametrize(
    "content",
    [
        "{not json",
        json.dumps({"claims": [{"id": "x", "pattern": "(unclosed", "title": "t", "fix": "f"}]}),
        json.dumps(
            {"claims": [{"id": "x", "pattern": "a", "title": "t", "fix": "f", "severity": "loud"}]}
        ),
        json.dumps({"claims": [{"id": "x", "pattern": "a", "title": "t"}]}),
    ],
)
def test_broken_rule_file_raises_a_clear_error(rules_dir, content):
    (rules_dir / "default.json").write_text(content)
    with pytest.raises(RuleFileError):
        load_rules(None)


def test_missing_default_file_raises(rules_dir):
    with pytest.raises(RuleFileError):
        load_rules(None)
