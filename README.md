# Local Hashtag Finder

A local Python application that analyses videos and generates relevant hashtags for TikTok, Instagram and YouTube Shorts.

The aim is to help creators find hashtags that relate to their actual video content, rather than relying on generic suggestions.

## Features

- **Video analysis:** Uses AI to understand the content of a video.
- **Audio transcription:** Converts spoken audio into text.
- **Hashtag generation:** Produces relevant hashtag suggestions based on the video.
- **Platform-specific suggestions:** Generates separate hashtag rankings for TikTok, Instagram and YouTube Shorts.
- **Local processing:** Uses locally running AI models instead of paid cloud APIs.
- **Text output:** Saves the results alongside the original video.

## Technologies

| Technology | Purpose |
|---|---|
| Python | Main application |
| FFmpeg | Extracts video frames and audio |
| Ollama | Runs AI models locally |
| Qwen 2.5 VL 3B | Analyses video frames and generates hashtags |
| Faster-Whisper | Transcribes audio |

## Requirements

- Python 3
- FFmpeg
- Ollama
- The `qwen2.5vl:3b` Ollama model
- Faster-Whisper

## Installation

**1. Install the dependencies**

Install FFmpeg and Ollama, then install the Python packages:

```bash
pip install ollama faster-whisper
```

**2. Download the AI model**

```bash
ollama pull qwen2.5vl:3b
```

Make sure Ollama is running before using the application.

**3. Run the application**

Navigate to the project directory and run:

```bash
python3 HashtagFinder.py "/path/to/video.mp4"
```

Supported video formats:

- MP4
- MOV
- WEBM
- MKV

## How it works

1. The application receives a video file.
2. FFmpeg extracts selected frames and the audio.
3. Faster-Whisper transcribes the audio.
4. Ollama analyses the video using the extracted frames and transcript.
5. The AI generates hashtag candidates.
6. The application scores and ranks hashtags for each platform.
7. The results are saved into a text file next to the original video.

## Output

The application creates a text file using the video's filename.

For example:

```text
video_hashtags.txt
```

The file contains the transcript, video analysis and generated hashtags for each supported platform.

## Limitations

- Hashtag scores are AI-generated estimates, not actual popularity or search-volume measurements.
- The application does not currently retrieve live trending hashtags.
- Hashtag recommendations may vary depending on the video and AI model.
- The current version is operated through the command line.

## Future plans

- Improve hashtag relevance and quality.
- Make recommendations more distinct between platforms.
- Improve error handling and testing.
- Create a graphical user interface.
- Add drag-and-drop video selection.
- Package the application as a standalone desktop application.

## Project status

Currently under development. The core video analysis, transcription and hashtag generation pipeline is working, with further improvements planned.