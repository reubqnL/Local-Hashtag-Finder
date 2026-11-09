import sys, subprocess, tempfile, json
from difflib import SequenceMatcher
from pathlib import Path
import ollama
from faster_whisper import WhisperModel

EXTS = ['.mp4', '.mov', '.webm', '.mkv']
FRAME_POINTS = [0.05, 0.2, 0.35, 0.5, 0.65, 0.8, 0.95]
PLATFORMS = ["TIKTOK", "INSTAGRAM", "YOUTUBE SHORTS"]
CATEGORIES = ["main", "niche", "community", "professional", "context"]

PLATFORM_CATEGORY_BONUS = {
    "TIKTOK": {"main": 0.4, "niche": 1.0, "community": 0.8, "professional": 0.1, "context": 0.3},
    "INSTAGRAM": {"main": 0.6, "niche": 0.6, "community": 0.8, "professional": 0.6, "context": 0.3},
    "YOUTUBE SHORTS": {"main": 1.0, "niche": 0.4, "community": 0.3, "professional": 0.2, "context": 0.6}
}

GENERIC_TAGS = {
    "#fyp", "#foryou", "#foryoupage", "#viral", "#viralvideo",
    "#trending", "#trendingnow", "#explore", "#explorepage",
    "#reels", "#shortsfeed", "#subscribe", "#follow",
    "#followme", "#likeforlikes"
}

MAX_TAGS = 8

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

    return transcript if transcript else "No speech detected."

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

Explain:
- The main subject and topic.
- What the person is discussing.
- The purpose of the video.
- Important people, organisations or places.
- Relevant activities or events shown.

Use the transcript as the main source of information.
Use the frames to understand the visual content.

Do not invent information or assume the topic from the filename.
If something is unclear, say so.

Keep the explanation detailed but concise.
""",
                "images": frames
            }
        ],
        options={"num_ctx": 8192}
    )

    return res["message"]["content"]

def generate_hashtag_candidates(description, title, transcript):
    print("generating hashtag candidates...")

    hashtag_schema = {
        "type": "object",
        "properties": {
            "hashtags": {
                "type": "array",
                "maxItems": 12,
                "items": {
                    "type": "object",
                    "properties": {
                        "tag": {"type": "string"},
                        "category": {"type": "string", "enum": CATEGORIES},
                        "relevance": {"type": "number"},
                        "specificity": {"type": "number"},
                        "platform_scores": {
                            "type": "object",
                            "properties": {
                                "TIKTOK": {"type": "number"},
                                "INSTAGRAM": {"type": "number"},
                                "YOUTUBE SHORTS": {"type": "number"}
                            },
                            "required": PLATFORMS
                        }
                    },
                    "required": [
                        "tag", "category", "relevance",
                        "specificity", "platform_scores"
                    ]
                }
            }
        },
        "required": ["hashtags"]
    }

    res = ollama.chat(
        model="qwen2.5vl:3b",
        messages=[
            {
                "role": "user",
                "content": f"""
Generate up to 12 useful hashtags for this video.

TITLE:
{title}

VIDEO ANALYSIS:
{description}

TRANSCRIPT:
{transcript}

Use a mix of these categories where relevant:
- main: the core subject
- niche: specific topics within the subject
- community: related audiences or communities
- professional: careers, skills and industries
- context: places, tools, events or formats

Only suggest tags that genuinely relate to the video.
Do not invent people, organisations or events.
Avoid repeating the same idea with slightly different wording.
Avoid generic tags such as #fyp, #viral and #trending.

For every tag, provide:
- relevance: 1-10
- specificity: 1-10
- platform_scores: separate 1-10 estimates for TikTok, Instagram and YouTube Shorts.

TikTok: consider niche communities and short-form discovery.
Instagram: consider searchable topics and interest communities.
YouTube Shorts: prioritise clear descriptive keywords.

Give each platform its own scores. These are estimates, not real popularity data.
Return the hashtags in the requested JSON format.
""",
            }
        ],
        format=hashtag_schema,
        options={"num_ctx": 8192, "num_predict": 1800, "temperature": 0.2}
    )

    data = json.loads(res["message"]["content"])
    candidates = []
    seen = set()

    for item in data.get("hashtags", []):
        tag = item.get("tag", "").strip()

        if not tag.startswith("#") or not tag[1:].replace("_", "").isalnum():
            continue

        if not tag[1:].isascii():
            continue

        if tag.lower() in seen or tag.lower() in GENERIC_TAGS:
            continue

        category = item["category"]

        relevance = max(0, min(10, float(item["relevance"])))
        specificity = max(0, min(10, float(item["specificity"])))

        scores = {
            platform: max(0, min(10, float(item["platform_scores"][platform])))
            for platform in PLATFORMS
        }

        if relevance == 0:
            continue

        candidates.append({
            "tag": tag,
            "category": category,
            "relevance": relevance,
            "specificity": specificity,
            "platform_scores": scores
        })

        seen.add(tag.lower())

    print(f"generated {len(candidates)} hashtag candidates")

    return candidates

def tags_overlap(tag, other):
    a = tag.lstrip("#").lower()
    b = other.lstrip("#").lower()

    if a in b or b in a:
        return True

    return SequenceMatcher(None, a, b).ratio() >= 0.75

def score_hashtags(candidates, platform):
    scored = []

    for item in candidates:
        relevance = item["relevance"]
        platform_score = item["platform_scores"][platform]
        specificity = item["specificity"]
        category = item["category"]

        score = relevance * 0.5 + platform_score * 0.35 + specificity * 0.15
        score += PLATFORM_CATEGORY_BONUS[platform].get(category, 0.3)

        scored.append({
            "tag": item["tag"],
            "score": score
        })

    scored.sort(key=lambda item: item["score"], reverse=True)

    selected = []

    for item in scored:
        if any(tags_overlap(item["tag"], tag) for tag in selected):
            continue

        selected.append(item["tag"])

        if len(selected) == MAX_TAGS:
            break

    return selected

def get_hashtags(description, title, transcript):
    candidates = generate_hashtag_candidates(description, title, transcript)

    if not candidates:
        return "\n\n".join(
            f"{platform}:\nNo relevant hashtags identified."
            for platform in PLATFORMS
        )

    results = []

    for platform in PLATFORMS:
        tags = score_hashtags(candidates, platform)

        if not tags:
            tags = ["No relevant hashtags identified."]

        print(f"{platform}: generated {len(tags)} hashtags")
        results.append(f"{platform}:\n{' '.join(tags)}")

    return "\n\n".join(results)

def save_results(video, description, transcript, hashtags):
    out = video.with_name(f"{video.stem}_hashtags.txt")

    with open(out, "w", encoding="utf-8") as file:
        file.write(f"VIDEO: {video.name}\n\n")
        file.write(f"VIDEO TRANSCRIPT:\n{transcript}\n\n")
        file.write(f"VIDEO ANALYSIS:\n{description}\n\n")
        file.write(
            "Scores are AI estimates of relevance and platform suitability, "
            "not real hashtag popularity, search volume or trends.\n\n"
        )
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