
import subprocess
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.services.audio_verifier import verify_audio
from backend.services.video_verifier import verify_video


router = APIRouter(
    prefix="/api/media",
    tags=["Media Compliance"],
)

MAX_UPLOAD_BYTES = 100 * 1024 * 1024

AUDIO_TYPES = {
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/aac",
    "audio/ogg",
    "audio/flac",
    "audio/webm",
}

VIDEO_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "video/webm",
    "video/x-matroska",
}


async def save_upload(
    file: UploadFile,
    allowed_types: set[str],
) -> Path:
    """Validate and save an uploaded media file."""
    if file.content_type not in allowed_types:
        await file.close()
        raise HTTPException(
            status_code=415,
            detail="Unsupported media type.",
        )

    suffix = Path(file.filename or "").suffix
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp:
            temp_path = Path(temp.name)
            total_bytes = 0

            while True:
                chunk = await file.read(1024 * 1024)

                if not chunk:
                    break

                total_bytes += len(chunk)

                if total_bytes > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail="Media file must not exceed 100 MB.",
                    )

                temp.write(chunk)

        if total_bytes == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty.",
            )

        return temp_path

    except Exception:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise

    finally:
        await file.close()


def extract_audio(video_path: Path, audio_path: Path) -> None:
    """Extract a video's audio track to a WAV file using FFmpeg."""
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-nostdin",
                "-v", "error",
                "-y",
                "-i", str(video_path),
                "-map", "0:a:0",
                "-vn",
                "-ac", "2",
                "-ar", "48000",
                "-c:a", "pcm_s16le",
                str(audio_path),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=180,
        )

    except FileNotFoundError as exc:
        raise RuntimeError(
            "FFmpeg is not installed or is not on PATH."
        ) from exc

    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Audio extraction timed out.") from exc

    except subprocess.CalledProcessError as exc:
        raise ValueError(
            "Audio extraction failed. The video may have no audio track "
            "or may be invalid."
        ) from exc


@router.post("/audio/scan")
async def scan_audio(
    file: UploadFile = File(...),
    target_lufs: float = Form(-24.0),
    tolerance_lu: float = Form(1.0),
):
    """Transcribe spoken content and measure integrated loudness."""
    path = await save_upload(file, AUDIO_TYPES)

    try:
        if tolerance_lu < 0:
            raise HTTPException(
                status_code=422,
                detail="tolerance_lu cannot be negative.",
            )

        result = verify_audio(
            str(path),
            target_lufs=target_lufs,
            tolerance_lu=tolerance_lu,
        )

        return {
            "filename": file.filename,
            **result,
        }

    except HTTPException:
        raise

    except (ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    finally:
        path.unlink(missing_ok=True)


@router.post("/video/scan")
async def scan_video(
    file: UploadFile = File(...),
    required_disclaimer: str = Form(...),
    target_lufs: float = Form(-24.0),
    tolerance_lu: float = Form(1.0),
):
    """Check scene transitions, disclaimer duration and audio."""
    video_path = await save_upload(file, VIDEO_TYPES)
    audio_path = None

    try:
        if not required_disclaimer.strip():
            raise HTTPException(
                status_code=422,
                detail="required_disclaimer cannot be empty.",
            )

        if tolerance_lu < 0:
            raise HTTPException(
                status_code=422,
                detail="tolerance_lu cannot be negative.",
            )

        video_result = verify_video(
            str(video_path),
            required_disclaimer,
        )

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav",
        ) as temp_audio:
            audio_path = Path(temp_audio.name)

        try:
            extract_audio(video_path, audio_path)

            audio_result = verify_audio(
                str(audio_path),
                target_lufs=target_lufs,
                tolerance_lu=tolerance_lu,
            )

        except ValueError as exc:
            # Do not treat missing or unextractable audio as a pass.
            audio_result = {
                "overall_status": "not_checked",
                "message": str(exc),
            }

        except RuntimeError as exc:
            raise HTTPException(
                status_code=500,
                detail=str(exc),
            ) from exc

        overall_status = (
            "pass"
            if (
                video_result["overall_status"] == "pass"
                and audio_result["overall_status"] == "pass"
            )
            else "review_required"
        )

        return {
            "filename": file.filename,
            "video_check": video_result,
            "audio_check": audio_result,
            "overall_status": overall_status,
        }

    except HTTPException:
        raise

    except (ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    finally:
        video_path.unlink(missing_ok=True)

        if audio_path is not None:
            audio_path.unlink(missing_ok=True)
