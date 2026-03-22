import json
from pathlib import Path
import chromadb

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TRANSCRIPTS_DIR = BASE_DIR / "data" / "transcripts"
CHROMA_DIR = BASE_DIR / "data" / "chroma"

CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# Initialize ChromaDB client with persistent storage
chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))


def chunk_text(text: str, chunk_size: int = 200, overlap: int = 50) -> list[str]:
    """
    Splits plain text into overlapping chunks of roughly chunk_size words.
    """
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap  # move forward with overlap

    return chunks


def index_transcript(video_id: str) -> int:
    """
    Reads the flat transcript, chunks it, and stores in ChromaDB.
    Returns the number of chunks indexed.
    """
    flat_path = TRANSCRIPTS_DIR / f"{video_id}.txt"
    if not flat_path.exists():
        raise FileNotFoundError(f"Flat transcript not found for video_id: {video_id}")

    with open(flat_path, "r", encoding="utf-8") as f:
        transcript_text = f.read()

    chunks = chunk_text(transcript_text)

    # Create or get collection for this video
    collection = chroma_client.get_or_create_collection(
        name=f"video_{video_id.replace('-', '_')}",
        metadata={"video_id": video_id}
    )

    # Add chunks to collection
    collection.add(
        documents=chunks,
        ids=[f"{video_id}_chunk_{i}" for i in range(len(chunks))]
    )

    return len(chunks)


def retrieve_context(video_id: str, question: str, n_results: int = 3) -> str:
    """
    Queries ChromaDB for the most relevant chunks given a question.
    Returns a single string of concatenated context chunks.
    """
    collection = chroma_client.get_or_create_collection(
        name=f"video_{video_id.replace('-', '_')}"
    )

    results = collection.query(
        query_texts=[question],
        n_results=n_results
    )

    # Flatten and join the retrieved chunks
    chunks = results["documents"][0]
    context = "\n\n".join(chunks)
    return context