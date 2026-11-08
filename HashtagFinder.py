import sys
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 HashtagFinder.py <video_path>", file=sys.stderr)
        sys.exit(1)

    video_path = Path(sys.argv[1].strip('"'))

    if not video_path.is_file():
        print(f"Error: File not found at {video_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Selected video: {video_path.name}")

if __name__ == "__main__":
    main()