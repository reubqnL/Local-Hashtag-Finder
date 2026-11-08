import sys, subprocess, tempfile
from pathlib import Path
import ollama

EXTS = ['.mp4', '.mov', '.webm', '.mkv']
TIMES = [5, 15, 30, 50]


def get_frames(video, tmp):
    imgs = []

    for t in TIMES:
        out = f"{tmp}/f_{t}.jpg"

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-ss", str(t),
                "-i", str(video),
                "-frames:v", "1",
                "-update", "1",
                "-vf", "scale=640:-1",
                out
            ],
            stdout=subprocess.DEVNULL
        )

        if Path(out).exists():
            imgs.append(out)

    return imgs

def ask_ai(frames):
    print("analysing video...")

    res = ollama.chat(
        model="qwen2.5vl:3b",
        messages=[
            {
                "role": "user",
                "content": "Describe what's happening in these frames. Include the main subject, setting and actions.",
                "images": frames
            }
        ],
        options={"num_ctx": 8192}
    )

    return res["message"]["content"]

def get_hashtags(description):
    print("getting tags...")

    txt = f"""
Based on this video description, generate 10 relevant hashtags for each platform:
TikTok, Instagram and YouTube Shorts.

Use a mix of broad and specific tags. Keep them relevant and don't claim they're trending.

Video:
{description}

Format:

TIKTOK:
#tag #tag

INSTAGRAM:
#tag #tag

YOUTUBE SHORTS:
#tag #tag
"""

    res = ollama.chat(
        model="qwen2.5vl:3b",
        messages=[
            {
                "role": "user",
                "content": txt
            }
        ],
        options={"num_ctx": 8192}
    )

    return res["message"]["content"]

def save_results(video, description, hashtags):
    out = video.with_name(f"{video.stem}_hashtags.txt")

    with open(out, "w", encoding="utf-8") as file:
        file.write(f"VIDEO: {video.name}\n\n")
        file.write(f"VIDEO ANALYSIS:\n{description}\n\n")
        file.write(f"GENERATED HASHTAGS:\n{hashtags}\n")

    print(f"saved to {out}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Need a video file path.")
        sys.exit(1)

    f = Path(sys.argv[1])

    if not f.is_file():
        print("Video file not found.")
        sys.exit(1)

    if f.suffix.lower() not in EXTS:
        print("Invalid video format.")
        sys.exit(1)

    with tempfile.TemporaryDirectory() as td:
        frames = get_frames(f, td)

        if not frames:
            print("No frames extracted.")
            sys.exit(1)

        description = ask_ai(frames)
        print("\n", description)

        hashtags = get_hashtags(description)
        print("\n", hashtags)

        save_results(f, description, hashtags)