
from io import BytesIO
from collections import Counter

import cv2
import numpy as np
import pytesseract

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)
from PIL import Image, ImageOps, UnidentifiedImageError
from skimage.color import rgb2lab, deltaE_ciede2000


MAX_IMAGE_PIXELS = 25_000_000
COLOR_DISTANCE_THRESHOLD = 15.0


class ImageVerificationError(ValueError):
    """Raised when an uploaded image cannot be processed."""


def load_image(image_bytes: bytes) -> Image.Image:
    """Validate the uploaded bytes and return a normalized RGB image."""

    if not image_bytes:
        raise ImageVerificationError("The uploaded image is empty.")

    try:
        with Image.open(BytesIO(image_bytes)) as source:
            if source.width * source.height > MAX_IMAGE_PIXELS:
                raise ImageVerificationError(
                    "Image is too large. Maximum is 25 megapixels."
                )

            source.verify()

        with Image.open(BytesIO(image_bytes)) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            image.load()
            return image

    except ImageVerificationError:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ImageVerificationError(
            "Invalid or unsupported image file."
        ) from exc


def extract_text(image: Image.Image) -> str:
    """Extract text from an RGB image using Tesseract OCR."""

    # Enlarge small images to improve OCR.
    width, height = image.size

    if max(width, height) < 1200:
        scale = min(2.0, 1200 / max(width, height))
        image = image.resize(
            (int(width * scale), int(height * scale)),
            Image.Resampling.LANCZOS,
        )

    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray)

    # Thresholding often helps with dark text on light backgrounds.
    gray_array = np.array(gray)
    _, thresholded = cv2.threshold(
        gray_array,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )

    text = pytesseract.image_to_string(
        thresholded,
        config="--oem 3 --psm 6",
        lang="eng",
    )

    return "\n".join(
        line.strip()
        for line in text.splitlines()
        if line.strip()
    )


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    """Convert #RRGGBB to an RGB tuple."""

    color = color.strip().lstrip("#")

    if len(color) != 6:
        raise ValueError(f"Invalid hex color: #{color}")

    try:
        return tuple(
            int(color[index:index + 2], 16)
            for index in (0, 2, 4)
        )
    except ValueError as exc:
        raise ValueError(f"Invalid hex color: #{color}") from exc


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    """Convert an RGB tuple to a hex color."""

    return "#{:02X}{:02X}{:02X}".format(*rgb)


def color_distance(
    rgb_a: tuple[int, int, int],
    rgb_b: tuple[int, int, int],
) -> float:
    """Calculate perceptual Delta-E 2000 between two RGB colors."""

    colors = np.array(
        [[rgb_a, rgb_b]],
        dtype=np.float64,
    ) / 255.0

    lab = rgb2lab(colors)

    distance = deltaE_ciede2000(
        lab[:, 0, :],
        lab[:, 1, :],
    )

    return float(distance[0])


def find_dominant_colors(
    image: Image.Image,
    number_of_colors: int = 5,
) -> list[dict]:
    """Return representative dominant colors using OpenCV k-means."""

    if not 1 <= number_of_colors <= 10:
        raise ValueError("number_of_colors must be between 1 and 10.")

    small = image.copy()
    small.thumbnail((160, 160))

    pixels = np.asarray(small, dtype=np.uint8).reshape(-1, 3)

    if len(pixels) == 0:
        raise ImageVerificationError("Image has no usable pixels.")

    # Limit cluster count for images with few unique colors.
    unique_pixels = np.unique(pixels, axis=0)
    cluster_count = min(number_of_colors, len(unique_pixels))

    if cluster_count == 1:
        centers = unique_pixels.astype(np.float32)
        counts = np.array([len(pixels)])
    else:
        samples = pixels.astype(np.float32)

        cv2.setRNGSeed(42)
        criteria = (
            cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
            30,
            0.5,
        )

        _, labels, centers = cv2.kmeans(
            samples,
            cluster_count,
            None,
            criteria,
            3,
            cv2.KMEANS_PP_CENTERS,
        )

        counts = np.bincount(
            labels.flatten(),
            minlength=cluster_count,
        )

    order = np.argsort(counts)[::-1]

    return [
        {
            "hex": rgb_to_hex(
                tuple(int(round(v)) for v in centers[index])
            ),
            "rgb": [
                int(round(v)) for v in centers[index]
            ],
            "percentage": round(
                100.0 * int(counts[index]) / len(pixels),
                2,
            ),
        }
        for index in order
    ]


def compare_brand_palette(
    dominant_colors: list[dict],
    approved_colors: list[str],
    threshold: float = COLOR_DISTANCE_THRESHOLD,
) -> dict:
    """Compare prominent image colors with the brand palette."""

    if not approved_colors:
        return {
            "status": "not_checked",
            "message": "No approved brand colors were supplied.",
            "matches": [],
            "unmatched_colors": [],
        }

    approved_rgb = [hex_to_rgb(c) for c in approved_colors]
    matches = []
    unmatched = []

    for item in dominant_colors:
        actual_rgb = tuple(item["rgb"])

        distances = [
            color_distance(actual_rgb, approved)
            for approved in approved_rgb
        ]

        best_index = int(np.argmin(distances))
        best_distance = distances[best_index]

        result = {
            "image_color": item["hex"],
            "nearest_approved_color": approved_colors[best_index],
            "delta_e": round(best_distance, 2),
            "percentage": item["percentage"],
        }

        if best_distance <= threshold:
            matches.append(result)
        else:
            unmatched.append(result)

    # Dominant colors are a heuristic, not proof of a brand violation.
    status = "review_required" if unmatched else "pass"

    return {
        "status": status,
        "threshold": threshold,
        "approved_colors": approved_colors,
        "matches": matches,
        "unmatched_colors": unmatched,
        "message": (
            "Some prominent colors differ from the approved palette."
            if unmatched
            else "All detected dominant colors are within the configured "
                 "color-distance threshold."
        ),
    }


def verify_image(
    image_bytes: bytes,
    approved_colors: list[str] | None = None,
) -> dict:
    """Run OCR and visual palette analysis on an uploaded image."""

    image = load_image(image_bytes)

    text = extract_text(image)
    dominant_colors = find_dominant_colors(image)

    palette_result = compare_brand_palette(
        dominant_colors,
        approved_colors or [],
    )

    flags = []

    if not text:
        flags.append({
            "type": "ocr",
            "severity": "info",
            "message": "No readable text detected. Manual review may be needed.",
        })

    if palette_result["status"] == "review_required":
        flags.append({
            "type": "brand_color",
            "severity": "warning",
            "message": palette_result["message"],
        })

    return {
        "extracted_text": text,
        "ocr_status": "success" if text else "no_text_detected",
        "dominant_colors": dominant_colors,
        "palette_check": palette_result,
        "flags": flags,
    }
