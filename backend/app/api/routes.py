import uuid
import json
import asyncio
from pathlib import Path
from functools import partial
from typing import Iterator
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Query
from fastapi.responses import StreamingResponse
import aiofiles

from app.services.ffmpeg_service import extract_audio, UPLOADS_DIR
from app.services.transcription_service import transcribe_audio
from app.services.llm.factory import get_llm_provider
from app.services.rag_service import index_transcript, retrieve_context
from pydantic import BaseModel

TRANSCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "transcripts"

router = APIRouter()

# In-memory job tracker
jobs = {}

JOBS_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "jobs.json"


def load_jobs():
    """Load jobs from disk into memory on startup."""
    global jobs
    if JOBS_FILE.exists():
        with open(JOBS_FILE, "r", encoding="utf-8") as f:
            jobs = json.load(f)


def save_jobs():
    """Persist current jobs dict to disk."""
    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)


# Load jobs on module import
load_jobs()


class ChatRequest(BaseModel):
    question: str


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
    save_jobs()
    return summary


async def run_summarization_task(video_id: str):
    try:
        await run_summarization(video_id)
        jobs[video_id]["status"] = "done"
        save_jobs()
    except Exception as e:
        jobs[video_id]["status"] = "failed"
        jobs[video_id]["error"] = str(e)
        save_jobs()


async def process_video(video_id: str, video_path: Path, filename: str, summarize: bool):
    loop = asyncio.get_event_loop()
    try:
        jobs[video_id]["status"] = "extracting_audio"
        save_jobs()
        audio_path = await extract_audio(video_id, video_path)

        jobs[video_id]["status"] = "transcribing"
        save_jobs()
        transcript_path = await loop.run_in_executor(
            None, partial(transcribe_audio, video_id, audio_path, filename)
        )
        jobs[video_id]["transcript_path"] = str(transcript_path)
        save_jobs()

        jobs[video_id]["status"] = "indexing"
        save_jobs()
        chunk_count = await loop.run_in_executor(
            None, partial(index_transcript, video_id)
        )
        jobs[video_id]["chunk_count"] = chunk_count
        save_jobs()

        if summarize:
            jobs[video_id]["status"] = "summarizing"
            save_jobs()
            await run_summarization(video_id)

        jobs[video_id]["status"] = "done"
        save_jobs()

    except Exception as e:
        jobs[video_id]["status"] = "failed"
        jobs[video_id]["error"] = str(e)
        save_jobs()

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
    save_jobs()

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

@router.post("/index/{video_id}")
async def index_video(video_id: str, background_tasks: BackgroundTasks):
    """Trigger ChromaDB indexing for an already transcribed video."""
    if video_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    if jobs[video_id]["status"] not in ["done"]:
        raise HTTPException(status_code=400, detail=f"Video must be fully transcribed first. Current status: {jobs[video_id]['status']}")

    # Check if already indexed
    if jobs[video_id].get("chunk_count"):
        raise HTTPException(status_code=400, detail=f"Video already indexed with {jobs[video_id]['chunk_count']} chunks.")

    # Check flat transcript exists
    flat_path = TRANSCRIPTS_DIR / f"{video_id}.txt"
    if not flat_path.exists():
        raise HTTPException(status_code=404, detail="Flat transcript not found. Cannot index without transcription.")

    async def run_indexing(video_id: str):
        try:
            loop = asyncio.get_event_loop()
            jobs[video_id]["status"] = "indexing"
            save_jobs()
            chunk_count = await loop.run_in_executor(
                None, partial(index_transcript, video_id)
            )
            jobs[video_id]["chunk_count"] = chunk_count
            jobs[video_id]["status"] = "done"
            save_jobs()
        except Exception as e:
            jobs[video_id]["status"] = "failed"
            jobs[video_id]["error"] = str(e)
            save_jobs()

    background_tasks.add_task(run_indexing, video_id)

    return {
        "video_id": video_id,
        "message": "Indexing started."
    }

@router.post("/chat/{video_id}")
async def chat_with_video(video_id: str, request: ChatRequest):
    """Chat with a video using RAG. Streams the response back token by token."""
    if video_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    if jobs[video_id]["status"] != "done":
        raise HTTPException(status_code=400, detail=f"Video not ready for chat. Current status: {jobs[video_id]['status']}")

    # Retrieve relevant context from ChromaDB
    context = retrieve_context(video_id, request.question)

    # Get LLM provider
    llm = get_llm_provider()

    # Stream generator
    def token_stream() -> Iterator[str]:
        for token in llm.chat_stream(context, request.question):
            yield token
        yield "\n"

    return StreamingResponse(token_stream(), media_type="text/plain")


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