import asyncio
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOADS_DIR = BASE_DIR / "data" / "uploads"
AUDIO_DIR = BASE_DIR / "data" / "audio"

# Ensure directories exist
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


async def extract_audio(video_id: str, video_path: Path) -> Path:
    """
    Extracts audio from a video file using FFmpeg.
    Returns the path to the extracted audio file.
    """
    audio_path = AUDIO_DIR / f"{video_id}.mp3"

    command = [
        "ffmpeg",
        "-i", str(video_path),   # Input video
        "-vn",                    # No video
        "-acodec", "mp3",         # Audio codec
        "-ar", "16000",           # Sample rate (16kHz optimal for Whisper)
        "-ac", "1",               # Mono channel
        "-b:a", "64k",            # Bitrate (lightweight)
        str(audio_path),
        "-y"                      # Overwrite if exists
    ]

    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {stderr.decode()}")

    return audio_path