import math

import cv2
import numpy as np
from skimage.color import rgb2lab, deltaE_ciede2000


# ---------- Colour helpers ----------

def hex_to_rgb(hex_code):
    h = hex_code.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(*[int(c) for c in rgb])


def delta_e(rgb1, rgb2):
    """Colour difference: 0 = identical, ~2 barely visible, 10+ clearly different."""
    lab1 = rgb2lab(np.array([[rgb1]], dtype=np.float64) / 255.0)
    lab2 = rgb2lab(np.array([[rgb2]], dtype=np.float64) / 255.0)
    return float(deltaE_ciede2000(lab1, lab2)[0][0])


def _lch(rgb):
    """Return (lightness, chroma, hue in degrees)."""
    lab = rgb2lab(np.array([[rgb]], dtype=np.float64) / 255.0)[0][0]
    chroma = math.hypot(lab[1], lab[2])
    hue = math.degrees(math.atan2(lab[2], lab[1])) % 360
    return lab[0], chroma, hue


def is_tint_or_shade(rgb, palette, hue_tolerance=20, min_chroma=15):
    """True if the colour is a lighter, darker or washed-out version of a palette colour."""
    _, chroma, hue = _lch(rgb)
    if chroma < min_chroma:            # almost grey, so hue means nothing
        return True
    for p in palette:
        _, p_chroma, p_hue = _lch(p)
        if p_chroma < min_chroma:      # white, black and grey have no hue to compare
            continue
        diff = abs(hue - p_hue)
        diff = min(diff, 360 - diff)
        if diff <= hue_tolerance:
            return True
    return False


def _is_neutral(rgb, tolerance=20):
    # white, black and grey have almost equal R, G and B
    return max(rgb) - min(rgb) < tolerance


# ---------- Dominant colours ----------

def dominant_colors(image_bgr, k=5):
    """Return [(rgb, share_of_image), ...] biggest first, using k-means."""
    small = cv2.resize(image_bgr, (120, 120), interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
    pixels = rgb.reshape(-1, 3).astype(np.float32)

    cv2.setRNGSeed(0)  # same result every run
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 3, cv2.KMEANS_PP_CENTERS)

    counts = np.bincount(labels.flatten(), minlength=k)
    shares = counts / counts.sum()
    order = np.argsort(-shares)
    return [(tuple(int(c) for c in centers[i]), float(shares[i])) for i in order]


# ---------- The check ----------

def check_colors(image_bgr, palette_hex, threshold=12, min_share=0.05,
                 allow_neutrals=True, allow_tints=True, require_primary=True,
                 source="image", timestamp=None):
    """
    Compare the dominant colours of an image with the brand palette.
    - threshold: Delta-E above this counts as "different from the palette"
    - min_share: ignore colours covering less than this share of the image
    - allow_neutrals: white, black and grey are always allowed
    - allow_tints: lighter or darker versions of a palette colour are allowed
      (use False for flat graphics and logos where exact colours matter)
    - require_primary: report if the first palette colour is missing
    """
    palette = [hex_to_rgb(h) for h in palette_hex]
    colors = dominant_colors(image_bgr)
    findings = []

    for rgb, share in colors:
        if share < min_share:
            continue  # ignore tiny colour areas (anti-aliasing, noise)
        if allow_neutrals and _is_neutral(rgb):
            continue
        distances = [delta_e(rgb, p) for p in palette]
        nearest = int(np.argmin(distances))
        if distances[nearest] > threshold and not (
            allow_tints and is_tint_or_shade(rgb, palette)
        ):
            findings.append({
                "rule": "Off-palette colour",
                "severity": "high" if distances[nearest] > 30 else "medium",
                "evidence": (f"{rgb_to_hex(rgb)} covers {share:.0%} of the image; "
                             f"nearest brand colour {palette_hex[nearest]} "
                             f"(Delta-E {distances[nearest]:.1f})"),
                "source": source,
                "timestamp": timestamp,
                "suggestion": f"Use a colour from the brand palette, such as {palette_hex[nearest]}.",
            })

    if require_primary and palette:
        closest = min(delta_e(rgb, palette[0]) for rgb, share in colors if share >= min_share)
        if closest > threshold:
            findings.append({
                "rule": "Primary brand colour missing",
                "severity": "medium",
                "evidence": f"No dominant colour is close to {palette_hex[0]}",
                "source": source,
                "timestamp": timestamp,
                "suggestion": f"Use the primary brand colour {palette_hex[0]}.",
            })

    return {
        "source": source,
        "dominant_colors": [{"hex": rgb_to_hex(c), "share": round(s, 2)} for c, s in colors],
        "findings": findings,
    }


def check_image_file(path, palette_hex, **kwargs):
    image = cv2.imread(path)
    if image is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    return check_colors(image, palette_hex, **kwargs)


def check_video_colors(video_path, palette_hex, **kwargs):
    from video import sample_frames  # imported here because video.py loads Whisper (slow)

    all_findings, seen = [], set()
    for timestamp, frame in sample_frames(video_path):
        result = check_colors(frame, palette_hex, source="video_frame",
                              timestamp=timestamp, **kwargs)
        for f in result["findings"]:
            key = (f["rule"], f["evidence"].split(" covers")[0])
            if key not in seen:  # report each problem once, at its first timestamp
                seen.add(key)
                all_findings.append(f)
    return {"source": "video_colors", "findings": all_findings}


if __name__ == "__main__":
    import json

    palette = ["#C82828", "#FFFFFF"]
    print(json.dumps(check_image_file("samples/poster1.jpg", palette), indent=2))