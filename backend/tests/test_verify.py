"""
BrandVerify Backend Unit Tests
"""

from backend.services.text_verifier import verify_text_compliance
from backend.services.image_verifier import calculate_delta_e


def test_claim_detection():
    sample_text = "BrandVerify engine is guaranteed to be 10X faster with zero downtime."
    diff = verify_text_compliance(sample_text)

    assert len(diff.flags) >= 2
    assert any(f.flag_type == "claim_substantiation" for f in diff.flags)

    snippets = [f.original_snippet.lower() for f in diff.flags]
    assert "10x faster" in snippets
    assert "zero downtime" in snippets


def test_clean_text_has_no_flags():
    diff = verify_text_compliance("Our team ships a new feature every month.")
    assert len(diff.flags) == 0


def test_custom_rule_flag():
    sample_text = "Standard clean brand headline."
    custom_rule = "Check if word 'guaranteed' is present."
    diff = verify_text_compliance(sample_text, custom_rule=custom_rule)

    assert any(f.flag_type == "custom_rule" for f in diff.flags)


def test_delta_e_identical_colors():
    white_rgb = (255, 255, 255)
    assert calculate_delta_e(white_rgb, white_rgb) == 0.0


def test_delta_e_divergent_colors():
    white_rgb = (255, 255, 255)
    black_rgb = (0, 0, 0)
    assert calculate_delta_e(white_rgb, black_rgb) > 5.0


def test_recommended_text_keeps_original_wording():
    sample_text = "Our engine is guaranteed to be 10X faster."
    diff = verify_text_compliance(sample_text)

    # Original words must still be there, with review notes added after them
    assert "guaranteed [REVIEW:" in diff.recommended_text
    assert "10X faster [REVIEW:" in diff.recommended_text
    # The original text itself must not change
    assert diff.original_text == sample_text
