from abc import ABC, abstractmethod


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