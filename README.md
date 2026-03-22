# Vidscribe

A local-first pipeline for converting videos into searchable transcripts, AI summaries, and interactive Q&A — all running on your machine with no cloud dependencies.

## What it does
- Extracts audio from video files via FFmpeg
- Transcribes audio locally using faster-whisper
- Indexes transcripts into a local vector store (ChromaDB) for semantic search
- Generates summaries and answers questions using a local LLM via LM Studio

## Tech Stack
- **FastAPI** — REST API and task orchestration
- **FFmpeg** — audio extraction from video containers
- **faster-whisper** — local speech-to-text with timestamp output
- **ChromaDB** — local vector store for RAG
- **LM Studio** — local LLM inference via OpenAI-compatible API (Vulkan/AMD GPU accelerated)

## Requirements
- Python 3.12+
- FFmpeg installed on system PATH
- LM Studio running locally with a model loaded

## Running the Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at `http://localhost:8000/docs`

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/upload` | Upload a video. Add `?summarize=true` to auto-summarize |
| GET | `/api/v1/status/{video_id}` | Check processing status |
| GET | `/api/v1/transcript/{video_id}` | Fetch structured transcript with timestamps |
| POST | `/api/v1/index/{video_id}` | Index transcript into ChromaDB for chat |
| POST | `/api/v1/summarize/{video_id}` | Trigger summarization for a transcribed video |
| GET | `/api/v1/summary/{video_id}` | Fetch AI-generated summary |
| POST | `/api/v1/chat/{video_id}` | Chat with a video (streams response) |

## LM Studio Configuration
Set your provider details in `backend/.env`:
```env
LLM_PROVIDER=lmstudio
LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1
LMSTUDIO_MODEL=your-model-name
LLM_CONTEXT_WINDOW=
SUMMARY_CHUNK_WORDS=
```

## Frontend
Coming soon — React/Vite