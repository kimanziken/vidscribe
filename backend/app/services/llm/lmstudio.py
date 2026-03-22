from openai import OpenAI
from app.services.llm.base import BaseLLMProvider


SUMMARIZATION_PROMPT = """You are an expert at summarizing video transcripts.
Given the transcript below, produce a structured summary with the following sections:

1. **Overview** - A 2-3 sentence high level summary of what the video is about.
2. **Key Points** - The main points covered, as a bullet list.
3. **Conclusion** - A 1-2 sentence wrap up of the key takeaway.

Keep the summary concise and factual. Do not add information that is not in the transcript.

TRANSCRIPT:
{transcript_text}
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

    def __init__(self, base_url: str, model: str):
        self.model = model
        self.client = OpenAI(
            base_url=base_url,
            api_key="lm-studio"
        )

    def summarize(self, transcript_text: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes video transcripts."
                },
                {
                    "role": "user",
                    "content": SUMMARIZATION_PROMPT.format(transcript_text=transcript_text)
                }
            ],
            temperature=0.3,
            max_tokens=1000
        )
        return response.choices[0].message.content

    def chat(self, context: str, question: str) -> str:
        response = self.client.chat.completions.create(
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
            max_tokens=1000
        )
        return response.choices[0].message.content