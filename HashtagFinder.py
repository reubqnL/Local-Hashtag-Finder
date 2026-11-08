import sys
from pathlib import Path
import subprocess
import tempfile

SUPPORTED_FORMATS = {".mp4", ".mov", ".webm", ".mkv"}
TIMESTAMPS = [5, 15, 30, 50]


def extract_frames(video_path, temp_dir_path):
    frames = []

    for ts in TIMESTAMPS:
        output = temp_dir_path / f"frame_{ts}.jpg"

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-ss", str(ts),
                "-i", str(video_path),
                "-frames:v", "1",
                "-vf", "scale=640:-1",
                str(output)
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        if output.is_file():
            frames.append(output)

    return frames


def main():
    if len(sys.argv) < 2:
        script_name = Path(__file__).name
        print(f"Usage: python3 {script_name} <video_path>", file=sys.stderr)
        sys.exit(1)

    video_path = Path(sys.argv[1])

    if not video_path.is_file():
        print(f"Error: File not found - {video_path}", file=sys.stderr)
        sys.exit(1)

    if video_path.suffix.lower() not in SUPPORTED_FORMATS:
        print(f"Error: Unsupported format {video_path.suffix}", file=sys.stderr)
        sys.exit(1)

    print(f"Processing: {video_path.name}")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        frames = extract_frames(video_path, temp_dir_path)

        if not frames:
            print("Error: Failed to extract any frames.", file=sys.stderr)
            sys.exit(1)

        print(f"Extracted {len(frames)} frames:")
        for frame in frames:
            print(f"  - {frame.name}")


if __name__ == "__main__":
    main()