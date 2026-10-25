import os, shutil, subprocess, tempfile
from pathlib import Path
import cv2
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from backend.api.rulebook_compliance import load_rules
from backend.services.compliance_checker import(
    check_text, check_colors, overall_status
)


router = APIRouter(tags=["Audio and Video Compliance"])
MAX_BYTES = 100 * 1024 * 1024
AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac", ".webm"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".mpeg", ".mpg"}

def save_upload(upload: UploadFile, folder: Path, allowed: set[str]) -> Path:
    ext = Path(upload.filename or "").suffix.lower()
    if ext not in allowed: raise HTTPException(400, f"Unsupported file extension: {ext}")
    dest, total = folder / f"input{ext}", 0
    with dest.open("wb") as out:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk: break
            total += len(chunk)
            if total > MAX_BYTES:
                out.close(); dest.unlink(missing_ok=True)
                raise HTTPException(413, "Media file must be 100 MB or smaller.")
            out.write(chunk)
    return dest

def transcribe(path: str) -> str:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise HTTPException(501, "Install transcription dependency: pip install faster-whisper")
    model = WhisperModel(os.getenv("BRANDVERIFY_WHISPER_MODEL", "base"), device="cpu", compute_type="int8")
    try:
        segments, _ = model.transcribe(path, vad_filter=True)
        return " ".join(s.text.strip() for s in segments).strip()
    except Exception as exc:
        raise HTTPException(422, f"Transcription failed: {exc}")

def extract_audio(video_path: str, audio_path: str):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg: raise HTTPException(501, "Install FFmpeg and add it to PATH for video scanning.")
    result = subprocess.run([ffmpeg, "-y", "-i", video_path, "-vn", "-ac", "1", "-ar", "16000", audio_path],
                            capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        raise HTTPException(422, "Could not extract video audio; verify the file has a supported audio track.")

def sample_frame_colors(path: str, max_frames: int = 8) -> list[str]:
    cap = cv2.VideoCapture(path)
    if not cap.isOpened(): return []
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    positions = sorted(set(int(i * max(total - 1, 0) / max(max_frames - 1, 1))
                           for i in range(min(max_frames, max(total, 1)))))
    colors = []
    try:
        for pos in positions:
            cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
            ok, frame = cap.read()
            if not ok or frame is None: continue
            small = cv2.resize(frame, (64, 64), interpolation=cv2.INTER_AREA)
            b, g, r = [int(round(x)) for x in small.reshape(-1, 3).mean(axis=0)]
            colors.append(f"#{r:02X}{g:02X}{b:02X}")
    finally: cap.release()
    return colors

@router.post("/api/compliance/audio")
async def audio_compliance(brand_id: str = Form(...), file: UploadFile = File(...)):
    rules = load_rules(brand_id)
    if not rules.get("approved"): raise HTTPException(409, "Admin must approve rules before scanning.")
    with tempfile.TemporaryDirectory(prefix="bv_audio_") as temp:
        path = save_upload(file, Path(temp), AUDIO_EXTS)
        transcript = transcribe(str(path))
        findings = check_text(transcript, rules)
        return {"brand_id": brand_id, "media_type": "audio", "transcript": transcript,
            "status": overall_status(findings), "findings": findings,
            "note": "Transcript checks only; this does not verify factual truth or music licensing."}

@router.post("/api/compliance/video")
async def video_compliance(brand_id: str = Form(...), file: UploadFile = File(...)):
    rules = load_rules(brand_id)
    if not rules.get("approved"): raise HTTPException(409, "Admin must approve rules before scanning.")
    with tempfile.TemporaryDirectory(prefix="bv_video_") as temp:
        folder = Path(temp)
        video = save_upload(file, folder, VIDEO_EXTS)
        audio = folder / "audio.wav"
        extract_audio(str(video), str(audio))
        transcript = transcribe(str(audio))
        audio_findings = check_text(transcript, rules)
        frame_colors = sample_frame_colors(str(video))
        visual_findings = check_colors(frame_colors, rules)
        findings = audio_findings + visual_findings
        return {"brand_id": brand_id, "media_type": "video", "transcript": transcript,
            "sampled_frame_colors": frame_colors, "status": overall_status(findings),
            "findings": findings,
            "note": "Frame average colors are rough screening signals, not reliable dominant-color/Delta-E results. Logo matching and OCR on video frames are not included."}
