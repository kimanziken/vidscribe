from abc import ABC, abstractmethod
from typing import Iterator


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.
    Any new provider must implement these methods.
    """

    @abstractmethod
    def summarize(self, transcript_text: str) -> str:
        """
        Takes a plain text transcript and returns a summary string.
        """
        pass

    @abstractmethod
    def chat(self, context: str, question: str) -> str:
        """
        Takes retrieved transcript context and a user question.
        Returns the model's response string.
        """
        pass

    @abstractmethod
    def chat_stream(self, context: str, question: str) -> Iterator[str]:
        """
        Same as chat but yields tokens one by one as they are generated.
        Returns an iterator of string tokens.
        """
        pass