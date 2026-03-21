import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
import aiofiles

from app.services.ffmpeg_service import extract_audio, UPLOADS_DIR

router = APIRouter()

# In-memory job tracker (simple for now)
jobs = {}


async def process_video(video_id: str, video_path: Path):
    """Background task that runs the full pipeline."""
    try:
        jobs[video_id]["status"] = "extracting_audio"
        audio_path = await extract_audio(video_id, video_path)
        jobs[video_id]["status"] = "done"
        jobs[video_id]["audio_path"] = str(audio_path)

    except Exception as e:
        jobs[video_id]["status"] = "failed"
        jobs[video_id]["error"] = str(e)


@router.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Accepts a video file upload and kicks off the processing pipeline."""

    # Validate file type
    allowed_types = ["video/mp4", "video/x-matroska", "video/avi", "video/quicktime"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    # Generate unique ID for this job
    video_id = str(uuid.uuid4())
    video_path = UPLOADS_DIR / f"{video_id}_{file.filename}"

    # Save uploaded file to disk
    async with aiofiles.open(video_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # Register job
    jobs[video_id] = {
        "video_id": video_id,
        "filename": file.filename,
        "status": "uploaded"
    }

    # Kick off background processing
    background_tasks.add_task(process_video, video_id, video_path)

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