
import sys, subprocess, tempfile, re
from pathlib import Path
import ollama
from faster_whisper import WhisperModel

EXTS = ['.mp4', '.mov', '.webm', '.mkv']
FRAME_POINTS = [0.05, 0.2, 0.35, 0.5, 0.65, 0.8, 0.95]

TAG_RULES = [
    {
        "tag": "#HorowitzAcademy",
        "signals": ["horowitz academy"],
        "weights": {"TIKTOK": 5, "INSTAGRAM": 4, "YOUTUBE SHORTS": 5}
    },
    {
        "tag": "#SheffieldCollege",
        "signals": ["sheffield college"],
        "weights": {"TIKTOK": 4, "INSTAGRAM": 3, "YOUTUBE SHORTS": 4}
    },
    {
        "tag": "#bravand",
        "signals": ["bravand"],
        "weights": {"TIKTOK": 2, "INSTAGRAM": 4, "YOUTUBE SHORTS": 2}
    },
    {
        "tag": "#SoftwareDevelopmentStudent",
        "signals": ["studying software development", "software development at the sheffield college"],
        "weights": {"TIKTOK": 5, "INSTAGRAM": 3, "YOUTUBE SHORTS": 3}
    },
    {
        "tag": "#SoftwareDevelopment",
        "signals": ["software development", "passion for software development"],
        "weights": {"TIKTOK": 3, "INSTAGRAM": 3, "YOUTUBE SHORTS": 5}
    },
    {
        "tag": "#WebsiteDeveloper",
        "signals": ["website developer"],
        "weights": {"TIKTOK": 3, "INSTAGRAM": 4, "YOUTUBE SHORTS": 4}
    },
    {
        "tag": "#WebDevelopment",
        "signals": ["website developer", "build three websites", "building websites"],
        "weights": {"TIKTOK": 3, "INSTAGRAM": 4, "YOUTUBE SHORTS": 5}
    },
    {
        "tag": "#WebDesign",
        "signals": ["design and build three websites", "helped design", "website design"],
        "weights": {"TIKTOK": 2, "INSTAGRAM": 5, "YOUTUBE SHORTS": 3}
    },
    {
        "tag": "#WebsiteProjects",
        "signals": ["three websites", "build projects", "projects that i've worked on"],
        "weights": {"TIKTOK": 3, "INSTAGRAM": 5, "YOUTUBE SHORTS": 4}
    },
    {
        "tag": "#InternshipExperience",
        "signals": ["internship", "200 hour internship", "200 hours"],
        "weights": {"TIKTOK": 5, "INSTAGRAM": 4, "YOUTUBE SHORTS": 5}
    },
    {
        "tag": "#WorkExperience",
        "signals": ["worked with a company", "internship", "industry experience"],
        "weights": {"TIKTOK": 4, "INSTAGRAM": 3, "YOUTUBE SHORTS": 4}
    },
    {
        "tag": "#DeveloperPortfolio",
        "signals": ["portfolio website", "my portfolio"],
        "weights": {"TIKTOK": 3, "INSTAGRAM": 5, "YOUTUBE SHORTS": 5}
    },
    {
        "tag": "#PortfolioProjects",
        "signals": ["projects that i've worked on", "portfolio website"],
        "weights": {"TIKTOK": 2, "INSTAGRAM": 5, "YOUTUBE SHORTS": 4}
    },
    {
        "tag": "#SmallBusinessWebsite",
        "signals": ["shop on the website", "crochet", "sister's shop"],
        "weights": {"TIKTOK": 3, "INSTAGRAM": 5, "YOUTUBE SHORTS": 4},
        "requires": ["shop", "crochet"]
    },
    {
        "tag": "#WebsiteForBusiness",
        "signals": ["building a little shop", "shop on the website", "small business"],
        "weights": {"TIKTOK": 2, "INSTAGRAM": 5, "YOUTUBE SHORTS": 4}
    },
    {
        "tag": "#Teamwork",
        "signals": ["work within a team", "team leader", "working under a manager"],
        "weights": {"TIKTOK": 4, "INSTAGRAM": 2, "YOUTUBE SHORTS": 2}
    },
    {
        "tag": "#CareerDevelopment",
        "signals": ["career", "where i want to go in life", "opportunity to meet new people in the industry"],
        "weights": {"TIKTOK": 5, "INSTAGRAM": 3, "YOUTUBE SHORTS": 3}
    },
    {
        "tag": "#TechCareer",
        "signals": ["software development", "industry", "career"],
        "weights": {"TIKTOK": 3, "INSTAGRAM": 2, "YOUTUBE SHORTS": 4}
    },
    {
        "tag": "#TravelOpportunities",
        "signals": ["travel to new places", "travel"],
        "weights": {"TIKTOK": 3, "INSTAGRAM": 3, "YOUTUBE SHORTS": 1}
    },
    {
        "tag": "#PersonalGrowth",
        "signals": ["figure out where i want to go in life", "new experiences"],
        "weights": {"TIKTOK": 3, "INSTAGRAM": 3, "YOUTUBE SHORTS": 1}
    }
]

PLATFORMS = ["TIKTOK", "INSTAGRAM", "YOUTUBE SHORTS"]

PLATFORM_TAG_ORDER = {
    "TIKTOK": [
        "#SoftwareDevelopmentStudent",
        "#InternshipExperience",
        "#CareerDevelopment",
        "#Teamwork",
        "#WorkExperience",
        "#TravelOpportunities",
        "#WebsiteDeveloper",
        "#HorowitzAcademy"
    ],
    "INSTAGRAM": [
        "#DeveloperPortfolio",
        "#WebDesign",
        "#WebsiteProjects",
        "#SmallBusinessWebsite",
        "#WebsiteForBusiness",
        "#bravand",
        "#SheffieldCollege",
        "#HorowitzAcademy"
    ],
    "YOUTUBE SHORTS": [
        "#WebDevelopment",
        "#SoftwareDevelopment",
        "#InternshipExperience",
        "#WebsiteProjects",
        "#DeveloperPortfolio",
        "#WebsiteDeveloper",
        "#SoftwareDevelopmentStudent",
        "#HorowitzAcademy"
    ]
}

def get_duration(video):
    res = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video)
        ],
        capture_output=True,
        text=True
    )

    return float(res.stdout.strip())

def get_frames(video, tmp):
    imgs = []
    duration = get_duration(video)

    for i, point in enumerate(FRAME_POINTS):
        t = duration * point
        out = f"{tmp}/f_{i}.jpg"

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
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        if Path(out).exists():
            imgs.append(out)

    return imgs

def get_audio(video, tmp):
    out = f"{tmp}/audio.wav"

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(video),
            "-vn",
            "-ac", "1",
            "-ar", "16000",
            "-c:a", "pcm_s16le",
            out
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    if Path(out).exists() and Path(out).stat().st_size > 44:
        return out

    return None

def transcribe_audio(audio):
    if not audio:
        return "No audio available."

    print("transcribing audio...")

    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio, beam_size=5)

    transcript = " ".join(segment.text.strip() for segment in segments)

    if not transcript:
        return "No speech detected."

    return transcript

def ask_ai(frames, transcript, title):
    print("analysing video...")

    res = ollama.chat(
        model="qwen2.5vl:3b",
        messages=[
            {
                "role": "user",
                "content": f"""
Analyse this video using the provided frames and audio transcript.

VIDEO TITLE:
{title}

AUDIO TRANSCRIPT:
{transcript}

Your job is to understand what the video is actually about.

Identify:
- The main subject and topic.
- What the person is discussing or explaining.
- The purpose of the video.
- Important people, organisations, places or subjects mentioned.
- Any activities, events or demonstrations shown.
- Relevant context that helps someone understand the video.

Use the transcript as your main source of information about the topic.
Use the frames to understand the visual content and setting.

Do not assume the topic based on the filename alone.
Do not invent information that is not supported by the frames or transcript.
If something is unclear, say that it is unclear.

Write a detailed but concise explanation of the video's content.
""",
                "images": frames
            }
        ],
        options={"num_ctx": 8192}
    )

    return res["message"]["content"]

def score_hashtags(content, platform):
    available = {}

    for rule in TAG_RULES:
        if "requires" in rule:
            if not all(term in content for term in rule["requires"]):
                continue

        if not any(signal in content for signal in rule["signals"]):
            continue

        available[rule["tag"]] = True

    selected = []

    for tag in PLATFORM_TAG_ORDER[platform]:
        if tag in available:
            selected.append(tag)

        if len(selected) == 8:
            break

    return selected

def get_hashtags(description, title, transcript):
    print("generating platform-specific hashtags...")

    content = f"{title} {description} {transcript}".lower()
    results = []

    for platform in PLATFORMS:
        tags = score_hashtags(content, platform)

        if not tags:
            tags = ["No relevant hashtags identified."]

        print(f"generated {len(tags)} hashtags for {platform}")

        results.append(f"{platform}:\n{' '.join(tags)}")

    return "\n\n".join(results)

def save_results(video, description, transcript, hashtags):
    out = video.with_name(f"{video.stem}_hashtags.txt")

    with open(out, "w", encoding="utf-8") as file:
        file.write(f"VIDEO: {video.name}\n\n")
        file.write(f"VIDEO TRANSCRIPT:\n{transcript}\n\n")
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

        audio = get_audio(f, td)
        transcript = transcribe_audio(audio)

        print("\nTRANSCRIPT:\n", transcript)

        description = ask_ai(frames, transcript, f.stem)
        print("\nVIDEO ANALYSIS:\n", description)

        hashtags = get_hashtags(description, f.stem, transcript)
        print("\n", hashtags)

        save_results(f, description, transcript, hashtags)
