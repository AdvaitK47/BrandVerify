import os
import sys

import pytest

# let the tests import ocr.py and video.py from the parent folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocr import extract_text
from video import process_video

POSTER = "samples/poster1.jpg"
VIDEO = "samples/video1.mp4"


@pytest.fixture(scope="module")
def video_result():
    # Whisper is slow, so process the video once and share the result
    return process_video(VIDEO)


# ---------- OCR ----------

def test_ocr_returns_expected_format():
    result = extract_text(POSTER)
    assert result["source"] == "ocr"
    assert isinstance(result["text"], str)
    assert 0 <= result["confidence"] <= 100

import os
import sys

import pytest

# let the tests import ocr.py and video.py from the parent folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocr import extract_text
from video import process_video

POSTER = "samples/poster1.jpg"
VIDEO = "samples/video1.mp4"


@pytest.fixture(scope="module")
def video_result():
    # Whisper is slow, so process the video once and share the result
    return process_video(VIDEO)


# ---------- OCR ----------

def test_ocr_returns_expected_format():
    result = extract_text(POSTER)
    assert result["source"] == "ocr"
    assert isinstance(result["text"], str)
    assert 0 <= result["confidence"] <= 100


def test_ocr_reads_known_words():
    text = extract_text(POSTER)["text"].upper()
    assert "CONTRAST" in text


def test_ocr_missing_file_raises_error():
    with pytest.raises(FileNotFoundError):
        extract_text("samples/does_not_exist.jpg")


# ---------- Video ----------

def test_video_returns_expected_format(video_result):
    assert video_result["source"] == "video"
    assert len(video_result["transcript"]) > 0
    for seg in video_result["transcript"]:
        assert {"start", "end", "text"} <= set(seg)


def test_video_transcript_catches_planted_claim(video_result):
    spoken = " ".join(s["text"] for s in video_result["transcript"]).lower()
    assert "guaranteed" in spoken


def test_video_frame_ocr_reads_on_screen_text(video_result):
    on_screen = " ".join(f["text"] for f in video_result["frame_text"]).upper()
    assert "GLOW" in on_screen
def test_ocr_reads_known_words():
    text = extract_text(POSTER)["text"].upper()
    assert "CONTRAST" in text


def test_ocr_missing_file_raises_error():
    with pytest.raises(FileNotFoundError):
        extract_text("samples/does_not_exist.jpg")


# ---------- Video ----------

def test_video_returns_expected_format(video_result):
    assert video_result["source"] == "video"
    assert len(video_result["transcript"]) > 0
    for seg in video_result["transcript"]:
        assert {"start", "end", "text"} <= set(seg)


def test_video_transcript_catches_planted_claim(video_result):
    spoken = " ".join(s["text"] for s in video_result["transcript"]).lower()
    assert "guaranteed" in spoken


def test_video_frame_ocr_reads_on_screen_text(video_result):
    on_screen = " ".join(f["text"] for f in video_result["frame_text"]).upper()
    assert "GLOW" in on_screen