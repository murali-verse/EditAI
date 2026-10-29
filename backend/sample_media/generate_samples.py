import os
import sys
import math
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import cv2
import numpy as np
import subprocess

from app.config import FFMPEG_PATH, SAMPLE_DIR

def generate_sample_assets():
    """Generates a complete multi-scene sample video and matching SRT subtitles."""
    video_path = SAMPLE_DIR / "sample_demo.mp4"
    srt_path = SAMPLE_DIR / "sample_demo.srt"
    audio_path = SAMPLE_DIR / "sample_bgm.wav"

    if video_path.exists() and srt_path.exists() and audio_path.exists():
        return str(video_path), str(srt_path), str(audio_path)

    print("Generating demo video with OpenCV & FFmpeg...")

    width, height = 854, 480
    fps = 25
    total_seconds = 30
    total_frames = fps * total_seconds

    temp_raw_avi = SAMPLE_DIR / "temp_raw.avi"
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    out = cv2.VideoWriter(str(temp_raw_avi), fourcc, fps, (width, height))

    scenes_def = [
        {"start": 0, "end": 10, "name": "Scene 1: Introduction & Motion", "color": (30, 40, 180)},
        {"start": 10, "end": 18, "name": "Scene 2: Slide Presentation", "color": (30, 140, 60)},
        {"start": 18, "end": 25, "name": "Scene 3: Target Segment (Split & Delete)", "color": (160, 40, 50)},
        {"start": 25, "end": 30, "name": "Scene 4: Finale & Outro", "color": (90, 30, 140)}
    ]

    for frame_idx in range(total_frames):
        sec = frame_idx / fps

        # Find current scene
        cur_scene = scenes_def[-1]
        for s in scenes_def:
            if s["start"] <= sec < s["end"]:
                cur_scene = s
                break

        # Base background with subtle gradient
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        c = cur_scene["color"]
        frame[:, :] = [c[0], c[1], c[2]]

        # Animated elements based on scene
        if cur_scene["start"] == 0:
            # High motion moving ball
            cx = int(width / 2 + math.sin(sec * 3) * 200)
            cy = int(height / 2 + math.cos(sec * 3) * 80)
            cv2.circle(frame, (cx, cy), 40, (255, 255, 255), -1)
            cv2.circle(frame, (cx, cy), 45, (0, 200, 255), 3)
        elif cur_scene["start"] == 10:
            # Static slide with subtle pulsing badge
            cv2.rectangle(frame, (80, 100), (width - 80, height - 100), (25, 25, 25), -1)
            cv2.rectangle(frame, (80, 100), (width - 80, height - 100), (80, 200, 120), 2)
            cv2.putText(frame, "SLIDE: DATA OVERVIEW", (120, 160), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 2)
            cv2.putText(frame, "Automated Scene Boundary Verification", (120, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        elif cur_scene["start"] == 18:
            # Segment intended for deletion / editing
            cv2.rectangle(frame, (50, 50), (width - 50, height - 50), (40, 20, 120), -1)
            cv2.putText(frame, "[ TARGET SEGMENT: 00:18 - 00:25 ]", (100, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            cv2.putText(frame, "Try: 'Split the clip at 00:20'", (120, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 255, 255), 2)
            cv2.putText(frame, "Or: 'Delete the selected segment'", (120, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 200, 100), 2)
        else:
            # Outro
            cv2.putText(frame, "AI Video Studio Complete", (150, 220), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
            cv2.putText(frame, "Export Ready", (320, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 200), 2)

        # Timecode overlay
        timecode_str = f"Time: {int(sec // 60):02d}:{sec % 60:05.2f} / 00:30.00"
        cv2.rectangle(frame, (20, 20), (380, 65), (10, 10, 10), -1)
        cv2.putText(frame, timecode_str, (30, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Scene label overlay
        cv2.putText(frame, cur_scene["name"], (30, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        out.write(frame)

    out.release()

    # Step 2: Generate synchronized audio tones using FFmpeg synth
    temp_audio = SAMPLE_DIR / "temp_audio.wav"
    cmd_audio = [
        FFMPEG_PATH, "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=440:duration=30:beep_factor=4",
        "-c:a", "pcm_s16le",
        str(temp_audio)
    ]
    subprocess.run(cmd_audio, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Step 3: Combine into H.264 / AAC MP4
    cmd_mux = [
        FFMPEG_PATH, "-y",
        "-i", str(temp_raw_avi),
        "-i", str(temp_audio),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        str(video_path)
    ]
    subprocess.run(cmd_mux, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Clean up temp raw video
    if temp_raw_avi.exists():
        temp_raw_avi.unlink()
    if temp_audio.exists():
        temp_audio.unlink()

    # Step 4: Write sample SRT subtitle file
    srt_content = """1
00:00:01,000 --> 00:00:08,000
Welcome to AI Video Studio - Intelligent Video Editor prototype.

2
00:00:10,500 --> 00:00:17,500
This is Scene 2 demonstrating automated scene analysis.

3
00:00:18,500 --> 00:00:24,500
This is the target segment from 00:18 to 00:25 for splitting and deleting.

4
00:00:25,500 --> 00:00:29,500
Export your final edited video with synchronized audio and subtitles.
"""
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content.strip())

    # Step 5: Generate an external BGM audio file
    cmd_bgm = [
        FFMPEG_PATH, "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=523.25:duration=30",
        "-af", "volume=0.4",
        "-c:a", "pcm_s16le",
        str(audio_path)
    ]
    subprocess.run(cmd_bgm, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print("Sample assets successfully generated.")
    return str(video_path), str(srt_path), str(audio_path)

if __name__ == "__main__":
    generate_sample_assets()
