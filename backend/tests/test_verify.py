"""
BrandVerify Backend Unit Tests
"""

import pytest
from backend.services.text_verifier import verify_text_compliance
from backend.services.image_verifier import calculate_delta_e

def test_superlative_detection():
    sample_text = "BrandVerify engine is guaranteed to be 10X faster with zero downtime."
    diff = verify_text_compliance(sample_text)
    
    assert len(diff.flags) >= 2
    assert any(f.flag_type == "superlative" for f in diff.flags)
    assert "3.8X" in diff.recommended_text or "99.99%" in diff.recommended_text

def test_custom_rule_flag():
    sample_text = "Standard clean brand headline."
    custom_rule = "Check if word 'guaranteed' is present."
    diff = verify_text_compliance(sample_text, custom_rule=custom_rule)
    
    assert any(f.flag_type == "custom_rule" for f in diff.flags)

def test_delta_e_identical_colors():
    white_rgb = (255, 255, 255)
    delta_e = calculate_delta_e(white_rgb, white_rgb)
    assert delta_e == 0.0

def test_delta_e_divergent_colors():
    white_rgb = (255, 255, 255)
    black_rgb = (0, 0, 0)
    delta_e = calculate_delta_e(white_rgb, black_rgb)
    assert delta_e > 5.0
