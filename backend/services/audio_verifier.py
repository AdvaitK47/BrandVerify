
import re
from pathlib import Path

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from faster_whisper import WhisperModel


DEFAULT_TARGET_LUFS = -24.0
DEFAULT_TOLERANCE_LU = 1.0

# A basic first-pass vocabulary scan, not an AI fact-checker.
RISK_PATTERNS = {
    "superlative": re.compile(
        r"\b("
        r"best|greatest|number\s+one|world[- ]class|"
        r"unbeatable|ultimate|perfect|"
        r"leading|fastest|safest|guaranteed"
        r")\b",
        re.IGNORECASE,
    ),
    "absolute_claim": re.compile(
        r"\b("
        r"100\s*%\s*guaranteed|"
        r"zero\s+risk|"
        r"always\s+works|"
        r"never\s+fails|"
        r"clinically\s+proven"
        r")\b",
        re.IGNORECASE,
    ),
}

# Load once per Python process, not once per request.
_whisper_model = None


def get_whisper_model(model_size="base", device="cpu"):
    global _whisper_model

    if _whisper_model is None:
        compute_type = "int8" if device == "cpu" else "float16"

        _whisper_model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
        )

    return _whisper_model


def transcribe_audio(audio_path: str) -> dict:
    """Transcribe speech and preserve segment timestamps."""

    path = Path(audio_path)

    if not path.is_file():
        raise ValueError("Audio file does not exist.")

    model = get_whisper_model()
    segments, info = model.transcribe(
        str(path),
        beam_size=5,
        vad_filter=True,
    )

    transcript_segments = []

    for segment in segments:
        text = segment.text.strip()

        if text:
            transcript_segments.append({
                "start": round(float(segment.start), 3),
                "end": round(float(segment.end), 3),
                "text": text,
            })

    transcript = " ".join(
        segment["text"] for segment in transcript_segments
    )

    return {
        "language": info.language,
        "language_probability": round(
            float(info.language_probability), 3
        ),
        "transcript": transcript,
        "segments": transcript_segments,
    }


def detect_spoken_risks(transcript: str) -> list[dict]:
    """Flag words and phrases that may require claims review."""

    flags = []

    for category, pattern in RISK_PATTERNS.items():
        for match in pattern.finditer(transcript):
            flags.append({
                "type": category,
                "matched_text": match.group(0),
                "start_char": match.start(),
                "end_char": match.end(),
                "severity": "review_required",
                "message": (
                    "Check this spoken statement against approved "
                    "brand sources and supporting evidence."
                ),
            })

    return flags


def measure_integrated_loudness(
    audio_path: str,
    target_lufs: float = DEFAULT_TARGET_LUFS,
    tolerance_lu: float = DEFAULT_TOLERANCE_LU,
) -> dict:
    """Measure integrated loudness according to BS.1770 metering."""

    audio, sample_rate = sf.read(
        audio_path,
        dtype="float64",
        always_2d=True,
    )

    if audio.size == 0:
        raise ValueError("Audio contains no samples.")

    if not np.all(np.isfinite(audio)):
        raise ValueError("Audio contains invalid numeric samples.")

    # Very short clips may not have enough audio for integrated metering.
    if len(audio) / sample_rate < 0.4:
        return {
            "status": "review_required",
            "integrated_lufs": None,
            "target_lufs": target_lufs,
            "tolerance_lu": tolerance_lu,
            "message": "Audio is too short for reliable loudness measurement.",
        }

    # Remove a singleton channel dimension for mono audio.
    samples = audio[:, 0] if audio.shape[1] == 1 else audio

    meter = pyln.Meter(sample_rate)
    loudness = float(meter.integrated_loudness(samples))

    if not np.isfinite(loudness):
        return {
            "status": "review_required",
            "integrated_lufs": None,
            "target_lufs": target_lufs,
            "tolerance_lu": tolerance_lu,
            "message": "Integrated loudness could not be measured reliably.",
        }

    lower = target_lufs - tolerance_lu
    upper = target_lufs + tolerance_lu
    passed = lower <= loudness <= upper

    return {
        "status": "pass" if passed else "review_required",
        "integrated_lufs": round(loudness, 2),
        "target_lufs": target_lufs,
        "tolerance_lu": tolerance_lu,
        "acceptable_range": [lower, upper],
        "message": (
            "Integrated loudness is within the configured target."
            if passed
            else "Integrated loudness is outside the configured target."
        ),
    }


def verify_audio(
    audio_path: str,
    target_lufs: float = DEFAULT_TARGET_LUFS,
    tolerance_lu: float = DEFAULT_TOLERANCE_LU,
) -> dict:
    """Run speech and loudness checks."""

    transcription = transcribe_audio(audio_path)

    speech_flags = detect_spoken_risks(
        transcription["transcript"]
    )

    loudness = measure_integrated_loudness(
        audio_path,
        target_lufs=target_lufs,
        tolerance_lu=tolerance_lu,
    )

    flags = list(speech_flags)

    if loudness["status"] != "pass":
        flags.append({
            "type": "loudness",
            "severity": "review_required",
            "message": loudness["message"],
        })

    return {
        "transcription": transcription,
        "spoken_claim_flags": speech_flags,
        "loudness_check": loudness,
        "flags": flags,
        "overall_status": (
            "review_required" if flags else "pass"
        ),
    }
