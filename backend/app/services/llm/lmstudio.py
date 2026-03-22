from typing import Iterator
from openai import OpenAI
from app.services.llm.base import BaseLLMProvider


CHUNK_SUMMARIZATION_PROMPT = """You are an expert at summarizing video transcripts.
Summarize the following transcript segment concisely, capturing the key points only.

TRANSCRIPT SEGMENT:
{transcript_text}
"""

FINAL_SUMMARIZATION_PROMPT = """You are an expert at summarizing video transcripts.
Below are partial summaries of different segments of a video transcript.
Combine them into a single structured summary with the following sections:

1. **Overview** - A 2-3 sentence high level summary of what the video is about.
2. **Key Points** - The main points covered, as a bullet list.
3. **Conclusion** - A 1-2 sentence wrap up of the key takeaway.

Keep the summary concise and factual. Do not add information not present in the partial summaries.

PARTIAL SUMMARIES:
{partial_summaries}
"""

CHAT_PROMPT = """You are a helpful assistant answering questions about a video.
Use only the transcript context provided below to answer the question.
If the answer is not in the context, say so honestly.

CONTEXT:
{context}

QUESTION:
{question}
"""


class LMStudioProvider(BaseLLMProvider):

    def __init__(self, base_url: str, model: str, context_window: int = 4096, summary_chunk_words: int = 600):
        self.model = model
        self.context_window = context_window
        self.summary_chunk_words = summary_chunk_words
        self.client = OpenAI(
            base_url=base_url,
            api_key="lm-studio"
        )

    def _chunk_text(self, text: str) -> list[str]:
        """Split text into chunks of summary_chunk_words words."""
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = start + self.summary_chunk_words
            chunks.append(" ".join(words[start:end]))
            start = end
        return chunks

    def _call(self, messages: list, temperature: float = 0.3, max_tokens: int = 1000) -> str:
        """Internal helper for non-streaming completions."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

    def summarize(self, transcript_text: str) -> str:
        """
        Summarizes transcript text using chunked summarization.
        If transcript fits in context window, summarizes directly.
        Otherwise summarizes each chunk then does a final pass.
        """
        words = transcript_text.split()

        # If transcript fits in context window, summarize directly
        if len(words) <= self.summary_chunk_words:
            return self._call([
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes video transcripts."
                },
                {
                    "role": "user",
                    "content": FINAL_SUMMARIZATION_PROMPT.format(partial_summaries=transcript_text)
                }
            ])

        # Otherwise chunk and summarize each chunk
        chunks = self._chunk_text(transcript_text)
        partial_summaries = []

        for i, chunk in enumerate(chunks):
            partial = self._call([
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes video transcripts."
                },
                {
                    "role": "user",
                    "content": CHUNK_SUMMARIZATION_PROMPT.format(transcript_text=chunk)
                }
            ])
            partial_summaries.append(f"Segment {i + 1}:\n{partial}")

        # Final pass — summarize the partial summaries
        combined = "\n\n".join(partial_summaries)
        return self._call([
            {
                "role": "system",
                "content": "You are a helpful assistant that summarizes video transcripts."
            },
            {
                "role": "user",
                "content": FINAL_SUMMARIZATION_PROMPT.format(partial_summaries=combined)
            }
        ])

    def chat(self, context: str, question: str) -> str:
        return self._call([
            {
                "role": "system",
                "content": "You are a helpful assistant answering questions about a video transcript."
            },
            {
                "role": "user",
                "content": CHAT_PROMPT.format(context=context, question=question)
            }
        ], temperature=0.5)

    def chat_stream(self, context: str, question: str) -> Iterator[str]:
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant answering questions about a video transcript."
                },
                {
                    "role": "user",
                    "content": CHAT_PROMPT.format(context=context, question=question)
                }
            ],
            temperature=0.5,
            max_tokens=1000,
            stream=True
        )

        for chunk in stream:
            token = chunk.choices[0].delta.content
            if token is not None:
                yield token