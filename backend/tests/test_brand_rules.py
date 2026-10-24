import json
import pytest
from backend.services.brand_rules import load_rules, load_all_rule_files, RuleFileError
from backend.services.text_verifier import verify_text_compliance
from backend.services.disclaimer_check import check_required_disclaimers

def test_load_rules_default_and_fallback():
    r_default = load_rules(None)
    assert r_default.brand_id == "default"
    assert len(r_default.claims) > 0

    r_none_str = load_rules("non-existent-brand")
    assert r_none_str.brand_id == "default"

def test_load_all_rule_files():
    all_rules = load_all_rule_files()
    expected_brands = {"default", "acme-tech", "luxe-fashion", "apex-fin", "pulse-health"}
    assert expected_brands.issubset(set(all_rules.keys()))

def test_text_verifier_brand_specific():
    text = "Our product is risk-free and clinically proven."
    
    # Apex Fin flags risk-free
    flags_apex = verify_text_compliance(text, rules=load_rules("apex-fin")).flags
    titles_apex = [f.title for f in flags_apex]
    assert "Absolute risk claim needs substantiation" in titles_apex

    # Pulse Health flags clinically proven
    flags_pulse = verify_text_compliance(text, rules=load_rules("pulse-health")).flags
    titles_pulse = [f.title for f in flags_pulse]
    assert "Clinical evidence claim needs substantiation" in titles_pulse

def test_disclaimer_check_brand_specific():
    text = "We expect revenue to double next quarter."
    
    # Luxe Fashion has no disclaimer rules
    flags_luxe = check_required_disclaimers(text, rules=load_rules("luxe-fashion"))
    assert len(flags_luxe) == 0

    # Acme Tech has forward-looking disclaimer rule
    flags_acme = check_required_disclaimers(text, rules=load_rules("acme-tech"))
    assert len(flags_acme) == 1
    assert flags_acme[0].flag_type == "missing_disclaimer"
