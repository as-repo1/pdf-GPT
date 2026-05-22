"""
OpenAI provider — supports any OpenAI-compatible API via configurable base_url.
Works with: OpenAI, Azure OpenAI, LM Studio, Groq, Together AI, etc.
"""

from typing import Iterator

from openai import OpenAI

_SYSTEM_TEMPLATE = (
    "You are a helpful AI assistant specialized in analyzing PDF documents. "
    "Answer the user's question using ONLY the context excerpts below. "
    "If the answer is not present in the context, say so clearly and honestly. "
    "Be concise, accurate, and cite relevant parts when helpful.\n\n"
    "--- Document Context ---\n{context}\n--- End Context ---"
)


class OpenAIProvider:
    """Chat provider backed by OpenAI (or any OpenAI-compatible endpoint)."""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url or None,
        )
        self.model = model

    def stream_chat(self, messages: list, context: str) -> Iterator[str]:
        system_msg = {"role": "system", "content": _SYSTEM_TEMPLATE.format(context=context)}
        payload = [system_msg] + messages

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=payload,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
