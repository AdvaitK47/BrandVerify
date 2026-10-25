import cv2
import whisper
from moviepy import VideoFileClip  # if this import fails: from moviepy.editor import VideoFileClip
from ocr import extract_text_from_image

_model = None

def process_video(video_path):
    transcript = transcribe(video_path)

    frame_text = []
    seen = set()
    for timestamp, frame in sample_frames(video_path):
        result = extract_text_from_image(frame)
        text = result["text"].strip()
        if text and text.lower() not in seen:   # skip repeated text
            seen.add(text.lower())
            frame_text.append({
                "timestamp": timestamp,
                "text": text,
                "confidence": result["confidence"],
            })

    return {"source": "video", "transcript": transcript, "frame_text": frame_text}

def transcribe(video_path):
    """Return the speech as a list of {start, end, text}."""
    global _model
    if _model is None:
        _model = whisper.load_model("base")  # use "tiny" if it is too slow

    audio_path = "temp_audio.wav"
    clip = VideoFileClip(video_path)
    if clip.audio is None:
        clip.close()
        return []
    clip.audio.write_audiofile(audio_path, logger=None)
    clip.close()

    result = _model.transcribe(audio_path)
    return [
        {"start": round(s["start"], 1), "end": round(s["end"], 1), "text": s["text"].strip()}
        for s in result["segments"]
    ]


def sample_frames(video_path, every_seconds=2):
    """Return a list of (timestamp_seconds, frame_image)."""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    step = int(fps * every_seconds)
    frames, i = [], 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if i % step == 0:
            frames.append((round(i / fps, 1), frame))
        i += 1
    cap.release()
    return frames


if __name__ == "__main__":
    import json
    print(json.dumps(process_video("samples/video1.mp4"), indent=2))