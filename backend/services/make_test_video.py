import os
import cv2
import numpy as np
import pyttsx3
from moviepy import VideoFileClip, AudioFileClip  # older moviepy: from moviepy.editor import ...

os.makedirs("samples", exist_ok=True)

SPEECH = "Try our new face cream. Guaranteed instant results in just one day!"
ON_SCREEN_TEXT = "GLOW CREAM - 50% OFF"

# 1. Make the speech
engine = pyttsx3.init()
engine.save_to_file(SPEECH, "temp_speech.wav")
engine.runAndWait()
audio = AudioFileClip("temp_speech.wav")

# 2. Make silent video frames with on-screen text
fps = 25
frames = int((audio.duration + 1) * fps)
out = cv2.VideoWriter("temp_silent.mp4", cv2.VideoWriter_fourcc(*"mp4v"), fps, (1280, 720))
for _ in range(frames):
    frame = np.full((720, 1280, 3), (40, 40, 200), np.uint8)
    cv2.putText(frame, ON_SCREEN_TEXT, (150, 330),
                cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5)
    out.write(frame)
out.release()

# 3. Join video and audio
clip = VideoFileClip("temp_silent.mp4")
try:
    final = clip.with_audio(audio)      # moviepy 2.x
except AttributeError:
    final = clip.set_audio(audio)       # moviepy 1.x
final.write_videofile("samples/video1.mp4", fps=fps)

# 4. Clean up
final.close()
audio.close()
clip.close()
for f in ("temp_speech.wav", "temp_silent.mp4"):
    if os.path.exists(f):
        os.remove(f)

print("Done: samples/video1.mp4")