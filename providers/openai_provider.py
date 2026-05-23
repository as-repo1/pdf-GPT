"""
OpenAI provider — supports any OpenAI-compatible API via configurable base_url.
Works with: OpenAI, Azure OpenAI, LM Studio, Groq, Together AI, etc.
"""

from typing import Iterator

from openai import APIError, OpenAI

_SYSTEM_TEMPLATE = (
    "You are a helpful AI assistant specialized in analyzing PDF documents. "
    "Answer the user's question using ONLY the context excerpts below. "
    "If the answer is not present in the context, say so clearly and honestly. "
    "Be concise, accurate, and cite relevant parts when helpful.\n\n"
    "--- Document Context ---\n{context}\n--- End Context ---"
)


def _friendly_openai_error(exc: APIError) -> str:
    """Convert an OpenAI API error into a concise, user-friendly message."""
    code = getattr(exc, "status_code", None)
    msg = str(exc)

    if code == 429 or "rate_limit" in msg.lower():
        return (
            "⏳ **Rate limit exceeded.**\n\n"
            "You've hit your API quota. Wait a moment and try again, "
            "or check your usage at [platform.openai.com](https://platform.openai.com/usage)."
        )

    if code == 401 or "authentication" in msg.lower() or "invalid_api_key" in msg.lower():
        return (
            "🔑 **Invalid API key.**\n\n"
            "Check your key in ⚙️ Settings → OpenAI → API Key."
        )

    if code == 404 or "model_not_found" in msg.lower():
        return (
            "❓ **Model not found.**\n\n"
            "The selected model doesn't exist or you don't have access. "
            "Try switching to `gpt-4o-mini` in ⚙️ Settings."
        )

    if code == 403:
        return (
            "🚫 **Access denied.**\n\n"
            "Your API key doesn't have permission to use this model or endpoint."
        )

    return f"**OpenAI API error ({code}):** {msg}"


class OpenAIProvider:
    """Chat provider backed by OpenAI (or any OpenAI-compatible endpoint)."""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url or None,
        )
        self.model = model

    def stream_chat(self, messages: list, context: str) -> Iterator[str]:
        system_msg = {
            "role": "system",
            "content": _SYSTEM_TEMPLATE.format(context=context),
        }
        payload = [system_msg] + messages

        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=payload,
                stream=True,
            )
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except APIError as exc:
            raise RuntimeError(_friendly_openai_error(exc)) from exc
