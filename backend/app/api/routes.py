import uuid
import json
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
import aiofiles

from app.services.ffmpeg_service import extract_audio, UPLOADS_DIR
from app.services.transcription_service import transcribe_audio
from app.services.llm.factory import get_llm_provider

from functools import partial
import asyncio

TRANSCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "transcripts"

router = APIRouter()

# In-memory job tracker
jobs = {}

async def process_video(video_id: str, video_path: Path, filename: str):
    """Background task that runs the full pipeline."""
    loop = asyncio.get_event_loop()
    try:
        # Phase 1: Extract audio (already async, no change)
        jobs[video_id]["status"] = "extracting_audio"
        audio_path = await extract_audio(video_id, video_path)

        # Phase 2: Transcribe (blocking → run in thread)
        jobs[video_id]["status"] = "transcribing"
        transcript_path = await loop.run_in_executor(
            None, partial(transcribe_audio, video_id, audio_path, filename)
        )
        jobs[video_id]["transcript_path"] = str(transcript_path)

        # Phase 3: Summarize (blocking → run in thread)
        jobs[video_id]["status"] = "summarizing"
        flat_path = TRANSCRIPTS_DIR / f"{video_id}.txt"
        with open(flat_path, "r", encoding="utf-8") as f:
            transcript_text = f.read()

        llm = get_llm_provider()
        summary_text = await loop.run_in_executor(
            None, partial(llm.summarize, transcript_text)
        )

        summary = {
            "video_id": video_id,
            "summary": summary_text
        }

        summary_path = TRANSCRIPTS_DIR / f"{video_id}_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        jobs[video_id]["status"] = "done"
        jobs[video_id]["transcript_path"] = str(transcript_path)
        jobs[video_id]["summary_path"] = str(summary_path)

    except Exception as e:
        jobs[video_id]["status"] = "failed"
        jobs[video_id]["error"] = str(e)
@router.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Accepts a video file upload and kicks off the processing pipeline."""

    allowed_types = ["video/mp4", "video/x-matroska", "video/avi", "video/quicktime"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    video_id = str(uuid.uuid4())
    video_path = UPLOADS_DIR / f"{video_id}_{file.filename}"

    async with aiofiles.open(video_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    jobs[video_id] = {
        "video_id": video_id,
        "filename": file.filename,
        "status": "uploaded"
    }

    background_tasks.add_task(process_video, video_id, video_path, file.filename)

    return {
        "video_id": video_id,
        "filename": file.filename,
        "status": "uploaded",
        "message": "Video received. Processing started."
    }


@router.get("/status/{video_id}")
async def get_status(video_id: str):
    """Check the processing status of a video job."""
    if video_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[video_id]


@router.get("/transcript/{video_id}")
async def get_transcript(video_id: str):
    """Fetch the structured transcript JSON for a completed job."""
    if video_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    if jobs[video_id]["status"] != "done":
        raise HTTPException(status_code=400, detail=f"Job not complete. Current status: {jobs[video_id]['status']}")

    transcript_path = Path(jobs[video_id]["transcript_path"])
    if not transcript_path.exists():
        raise HTTPException(status_code=404, detail="Transcript file not found")

    with open(transcript_path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/summary/{video_id}")
async def get_summary(video_id: str):
    """Fetch the AI generated summary for a completed job."""
    if video_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    if jobs[video_id]["status"] != "done":
        raise HTTPException(status_code=400, detail=f"Job not complete. Current status: {jobs[video_id]['status']}")

    summary_path = Path(jobs[video_id]["summary_path"])
    if not summary_path.exists():
        raise HTTPException(status_code=404, detail="Summary file not found")

    with open(summary_path, "r", encoding="utf-8") as f:
        return json.load(f)