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
    print("Running Ollama...")

    txt = (
        "Look at these frames and tell me what's happening in the video (subject, setting, actions). Be specific.")

    res = ollama.chat(
        model="qwen2.5vl:3b",
        messages=[
            {
                "role": "user",
                "content": txt,
                "images": frames
            }
        ],
        options={
            "num_ctx": 8192
        }
    )

    return res["message"]["content"]


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

    print(f"Working on {f.name}...")

    with tempfile.TemporaryDirectory() as td:
        frames = get_frames(f, td)

        # print(f"test, extracted {len(frames)} frames. paths: {frames}")


        if not frames:
            print("No frames extracted.")
            sys.exit(1)

        print(ask_ai(frames))