import uuid
import json
import asyncio
from pathlib import Path
from functools import partial
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Query
import aiofiles

from app.services.ffmpeg_service import extract_audio, UPLOADS_DIR
from app.services.transcription_service import transcribe_audio
from app.services.llm.factory import get_llm_provider

TRANSCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "transcripts"

router = APIRouter()

# In-memory job tracker
jobs = {}


async def run_summarization(video_id: str):
    """Runs summarization for a given video_id. Can be called from upload or standalone."""
    loop = asyncio.get_event_loop()

    flat_path = TRANSCRIPTS_DIR / f"{video_id}.txt"
    if not flat_path.exists():
        raise FileNotFoundError(f"Flat transcript not found for video_id: {video_id}")

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

    jobs[video_id]["summary_path"] = str(summary_path)
    return summary


async def process_video(video_id: str, video_path: Path, filename: str, summarize: bool):
    """Background task that runs the full pipeline."""
    loop = asyncio.get_event_loop()
    try:
        # Phase 1: Extract audio
        jobs[video_id]["status"] = "extracting_audio"
        audio_path = await extract_audio(video_id, video_path)

        # Phase 2: Transcribe
        jobs[video_id]["status"] = "transcribing"
        transcript_path = await loop.run_in_executor(
            None, partial(transcribe_audio, video_id, audio_path, filename)
        )
        jobs[video_id]["transcript_path"] = str(transcript_path)

        # Phase 3: Summarize (optional)
        if summarize:
            jobs[video_id]["status"] = "summarizing"
            await run_summarization(video_id)

        jobs[video_id]["status"] = "done"

    except Exception as e:
        jobs[video_id]["status"] = "failed"
        jobs[video_id]["error"] = str(e)


@router.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    summarize: bool = Query(default=False, description="Whether to auto-summarize after transcription")
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
        "status": "uploaded",
        "summarize_requested": summarize
    }

    background_tasks.add_task(process_video, video_id, video_path, file.filename, summarize)

    return {
        "video_id": video_id,
        "filename": file.filename,
        "status": "uploaded",
        "summarize_requested": summarize,
        "message": "Video received. Processing started."
    }


@router.post("/summarize/{video_id}")
async def summarize_video(video_id: str, background_tasks: BackgroundTasks):
    """Trigger summarization for an already transcribed video."""
    if video_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    if jobs[video_id]["status"] not in ["done"]:
        raise HTTPException(status_code=400, detail=f"Video must be fully transcribed first. Current status: {jobs[video_id]['status']}")

    summary_path = TRANSCRIPTS_DIR / f"{video_id}_summary.json"
    if summary_path.exists():
        raise HTTPException(status_code=400, detail="Summary already exists. Fetch it via GET /summary/{video_id}")

    jobs[video_id]["status"] = "summarizing"
    background_tasks.add_task(run_summarization_task, video_id)

    return {
        "video_id": video_id,
        "message": "Summarization started."
    }


async def run_summarization_task(video_id: str):
    """Wrapper for background task so status is reset to done after."""
    try:
        await run_summarization(video_id)
        jobs[video_id]["status"] = "done"
    except Exception as e:
        jobs[video_id]["status"] = "failed"
        jobs[video_id]["error"] = str(e)


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

    if jobs[video_id]["status"] not in ["done", "summarizing"]:
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

    summary_path = TRANSCRIPTS_DIR / f"{video_id}_summary.json"
    if not summary_path.exists():
        raise HTTPException(status_code=404, detail="Summary not found. Trigger it via POST /summarize/{video_id}")

    with open(summary_path, "r", encoding="utf-8") as f:
        return json.load(f)