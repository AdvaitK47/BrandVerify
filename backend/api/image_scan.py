
import json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.services.image_verifier import (
    ImageVerificationError,
    verify_image,
)

router = APIRouter(
    prefix="/api/images",
    tags=["Image Compliance"],
)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


@router.post("/scan")
async def scan_image(
    file: UploadFile = File(...),
    brand_id: str = Form(...),
    approved_colors: str = Form(...),
):
    """Scan an image for embedded text and brand color compliance."""

    if not brand_id.strip():
        raise HTTPException(400, "A brand must be selected.")

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            415,
            "Upload a JPEG, PNG, or WebP image.",
        )

    # Read at most 1 byte beyond the limit to detect oversized uploads.
    image_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()

    if not image_bytes:
        raise HTTPException(400, "The uploaded image is empty.")

    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            413,
            "Image must be no larger than 10 MB.",
        )

    
    try:
        try:
            colors = json.loads(approved_colors)
        except json.JSONDecodeError:
            # Also accept comma-separated colors.
            colors = [
                color.strip()
                for color in approved_colors.split(",")
                if color.strip()
            ]

        if (
            not isinstance(colors, list)
            or not colors
            or not all(
                isinstance(color, str)
                and len(color.strip().lstrip("#")) == 6
                and all(
                    c in "0123456789abcdefABCDEF"
                    for c in color.strip().lstrip("#")
                )
                for color in colors
            )
        ):
            raise ValueError(
                "approved_colors must contain a non-empty list of valid hex colors."
            )

        result = verify_image(
            image_bytes=image_bytes,
            approved_colors=colors,
        )

        return {
            "brand_id": brand_id,
            "filename": file.filename,
            **result,
        }

    except ImageVerificationError as exc:
        raise HTTPException(422, str(exc))
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    
    except Exception as exc:
        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"{type(exc).__name__}: {exc}",
        ) from exc


    except json.JSONDecodeError:
        raise HTTPException(
            422,
            'approved_colors must be JSON, e.g. ["#111111", "#FFFFFF"].',
        )
    except ImageVerificationError as exc:
        raise HTTPException(422, str(exc))
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    except Exception as exc:
        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"{type(exc).__name__}: {exc}",
        ) from exc
