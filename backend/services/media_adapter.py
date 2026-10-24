from ocr import extract_text
from video import process_video
from color_check import check_image_file, check_video_colors


def analyze_image(path, palette):
    ocr = extract_text(path)
    colors = check_image_file(path, palette)
    return {
        "items": [{"source": "ocr", "timestamp": None, "text": ocr["text"],
                   "confidence": ocr["confidence"]}],
        "findings": colors["findings"],
    }


def analyze_video(path, palette):
    video = process_video(path)
    items = [{"source": "audio", "timestamp": s["start"], "text": s["text"]}
             for s in video["transcript"]]
    items += [{"source": "frame_ocr", "timestamp": f["timestamp"], "text": f["text"],
               "confidence": f["confidence"]} for f in video["frame_text"]]
    colors = check_video_colors(path, palette)
    return {"items": items, "findings": colors["findings"]}