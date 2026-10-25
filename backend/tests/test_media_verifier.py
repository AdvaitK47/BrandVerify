
import pytest

from backend.services.audio_verifier import (
    detect_spoken_risks,
    transcribe_audio,
)
from backend.services.video_verifier import (
    VideoVerificationError,
    detect_scenes,
    normalize_text,
)


def test_superlative_claim_is_flagged():
    flags = detect_spoken_risks(
        "This is the best product on the market."
    )

    assert any(
        flag["type"] == "superlative"
        and flag["matched_text"].lower() == "best"
        for flag in flags
    )


def test_guaranteed_claim_is_flagged():
    flags = detect_spoken_risks(
        "100% guaranteed results."
    )

    assert len(flags) >= 1


def test_normal_sentence_has_no_risk_flags():
    flags = detect_spoken_risks(
        "Our product comes in three colors."
    )

    assert flags == []


def test_normalize_disclaimer_text():
    result = normalize_text(
        "Terms & Conditions Apply!"
    )

    assert result == "terms conditions apply"


def test_normalize_text_ignores_case_and_punctuation():
    assert normalize_text("PLEASE READ THIS.") == "please read this"


def test_transcription_rejects_missing_file():
    with pytest.raises(ValueError, match="does not exist"):
        transcribe_audio("samples/does_not_exist.wav")


def test_scene_detection_rejects_missing_file():
    with pytest.raises(VideoVerificationError, match="does not exist"):
        detect_scenes("samples/does_not_exist.mp4")
