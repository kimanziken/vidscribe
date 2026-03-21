import json
from pathlib import Path
from faster_whisper import WhisperModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TRANSCRIPTS_DIR = BASE_DIR / "data" / "transcripts"

TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

# Load model once at module level (avoids reloading on every request)
model = WhisperModel("base", device="cpu", compute_type="int8")


def transcribe_audio(video_id: str, audio_path: Path, filename: str) -> Path:
    """
    Transcribes audio using faster-whisper and saves structured JSON transcript.
    Returns the path to the transcript JSON file.
    """
    segments, info = model.transcribe(
        str(audio_path),
        beam_size=5,
        word_timestamps=False
    )

    transcript_segments = []
    for i, segment in enumerate(segments):
        transcript_segments.append({
            "id": i,
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": segment.text.strip()
        })

    transcript = {
        "video_id": video_id,
        "filename": filename,
        "duration": round(info.duration, 2),
        "language": info.language,
        "segments": transcript_segments
    }

    transcript_path = TRANSCRIPTS_DIR / f"{video_id}.json"
    with open(transcript_path, "w", encoding="utf-8") as f:
        json.dump(transcript, f, indent=2, ensure_ascii=False)

    return transcript_path