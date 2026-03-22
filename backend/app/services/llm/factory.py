import os
from dotenv import load_dotenv
from app.services.llm.base import BaseLLMProvider
from app.services.llm.lmstudio import LMStudioProvider

load_dotenv()


def get_llm_provider() -> BaseLLMProvider:
    """
    Reads LLM_PROVIDER from .env and returns the appropriate provider instance.
    Add new providers here as elif blocks.
    """
    provider = os.getenv("LLM_PROVIDER", "lmstudio").lower()

    if provider == "lmstudio":
        return LMStudioProvider(
            base_url=os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1"),
            model=os.getenv("LMSTUDIO_MODEL", "qwen2.5-coder-1.5b-instruct"),
            context_window=int(os.getenv("LLM_CONTEXT_WINDOW", "4096")),
            summary_chunk_words=int(os.getenv("SUMMARY_CHUNK_WORDS", "600"))
        )

    # Future providers:
    # elif provider == "ollama":
    #     return OllamaProvider(...)
    # elif provider == "openai":
    #     return OpenAIProvider(...)

    raise ValueError(f"Unknown LLM provider: '{provider}'. Check your .env LLM_PROVIDER value.")