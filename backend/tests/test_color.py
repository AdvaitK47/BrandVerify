import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from color_check import check_colors, delta_e

RED_BGR = (40, 40, 200)  # OpenCV uses BGR, so this is RGB (200, 40, 40) = #C82828


def solid(bgr):
    return np.full((300, 300, 3), bgr, np.uint8)


def test_delta_e_identical_colours_is_zero():
    assert delta_e((200, 40, 40), (200, 40, 40)) < 0.01


def test_matching_palette_has_no_findings():
    result = check_colors(solid(RED_BGR), ["#C82828"])
    assert result["findings"] == []


def test_wrong_palette_is_flagged():
    result = check_colors(solid(RED_BGR), ["#1E50C8"])  # blue palette
    rules = [f["rule"] for f in result["findings"]]
    assert "Off-palette colour" in rules


def test_off_brand_block_is_found():
    img = solid(RED_BGR)
    img[:, :120] = (0, 200, 0)  # green strip, about 40% of the image
    result = check_colors(img, ["#C82828"])
    assert any(f["rule"] == "Off-palette colour" for f in result["findings"])


def test_dark_shade_of_brand_colour_is_allowed():
    dark_red_bgr = (30, 30, 110)  # a darker version of the brand red
    result = check_colors(solid(dark_red_bgr), ["#C82828"])
    assert not any(f["rule"] == "Off-palette colour" for f in result["findings"])


def test_white_in_palette_does_not_excuse_pink():
    pink_bgr = (180, 60, 230)  # RGB (230, 60, 180), a magenta pink
    result = check_colors(solid(pink_bgr), ["#C82828", "#FFFFFF"])
    assert any(f["rule"] == "Off-palette colour" for f in result["findings"])