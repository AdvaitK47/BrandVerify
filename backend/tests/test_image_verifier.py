
from io import BytesIO

import pytest
from PIL import Image

from backend.services.image_verifier import (
    ImageVerificationError,
    compare_brand_palette,
    color_distance,
    find_dominant_colors,
    load_image,
    verify_image,
)


def create_test_image(color="white"):
    """Create an in-memory PNG image."""
    image = Image.new("RGB", (100, 100), color=color)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_load_valid_image():
    image = load_image(create_test_image())

    assert image.size == (100, 100)
    assert image.mode == "RGB"


def test_reject_empty_image():
    with pytest.raises(ImageVerificationError):
        load_image(b"")


def test_reject_invalid_image():
    with pytest.raises(ImageVerificationError):
        load_image(b"this is not an image")


def test_identical_colors_have_zero_distance():
    distance = color_distance((255, 0, 0), (255, 0, 0))

    assert distance == pytest.approx(0.0, abs=0.01)


def test_dominant_color_is_detected():
    image = load_image(create_test_image("#FF0000"))
    colors = find_dominant_colors(image, number_of_colors=3)

    assert len(colors) >= 1
    assert colors[0]["hex"] == "#FF0000"
    assert colors[0]["percentage"] == pytest.approx(100.0)


def test_approved_color_palette_passes():
    image = load_image(create_test_image("#FF0000"))
    dominant = find_dominant_colors(image, number_of_colors=3)

    result = compare_brand_palette(
        dominant,
        ["#FF0000", "#FFFFFF"],
    )

    assert result["status"] == "pass"
    assert result["unmatched_colors"] == []


def test_unapproved_color_is_flagged():
    image = load_image(create_test_image("#FF0000"))
    dominant = find_dominant_colors(image, number_of_colors=3)

    result = compare_brand_palette(
        dominant,
        ["#0000FF", "#FFFFFF"],
    )

    assert result["status"] == "review_required"
    assert len(result["unmatched_colors"]) >= 1


def test_missing_palette_is_not_checked():
    image = load_image(create_test_image())
    dominant = find_dominant_colors(image, number_of_colors=3)

    result = compare_brand_palette(dominant, [])

    assert result["status"] == "not_checked"


def test_complete_image_verification():
    result = verify_image(
        create_test_image("#FFFFFF"),
        approved_colors=["#FFFFFF", "#000000"],
    )

    assert "extracted_text" in result
    assert "dominant_colors" in result
    assert "palette_check" in result
    assert "flags" in result
