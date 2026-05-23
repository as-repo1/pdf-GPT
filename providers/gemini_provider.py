"""
Google Gemini provider using the modern google-genai SDK.
Supports system instructions and streaming multi-turn conversations.
"""

import re
from typing import Iterator

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

_SYSTEM_TEMPLATE = (
    "You are a helpful AI assistant specialized in analyzing PDF documents. "
    "Answer the user's question using ONLY the context excerpts below. "
    "If the answer is not present in the context, say so clearly and honestly. "
    "Be concise, accurate, and cite relevant parts when helpful.\n\n"
    "--- Document Context ---\n{context}\n--- End Context ---"
)


def _friendly_gemini_error(exc: genai_errors.APIError) -> str:
    """Convert a Gemini API error into a concise, user-friendly message."""
    msg = str(exc)

    # Rate limit / quota exhausted
    if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
        # Try to extract the retry delay
        match = re.search(r"retry(?:\s+in|Delay[\":\s]+)[\s\"]*(\d+)", msg, re.IGNORECASE)
        wait = f" Try again in ~{match.group(1)}s." if match else ""
        return (
            "⏳ **Gemini rate limit exceeded.**\n\n"
            f"You've hit your API quota for this model.{wait}\n\n"
            "💡 **Options:**\n"
            "- Wait a moment and try again\n"
            "- Switch to a different Gemini model (e.g. `gemini-1.5-flash`)\n"
            "- Check your quota at [ai.dev/rate-limit](https://ai.dev/rate-limit)"
        )

    # Invalid API key
    if "UNAUTHENTICATED" in msg or "401" in msg or "API_KEY_INVALID" in msg:
        return (
            "🔑 **Invalid Gemini API key.**\n\n"
            "Check your key in ⚙️ Settings.\n"
            "Get a free key → [aistudio.google.com](https://aistudio.google.com)"
        )

    # Permission denied
    if "PERMISSION_DENIED" in msg or "403" in msg:
        return (
            "🚫 **Permission denied by Gemini API.**\n\n"
            "Your API key may not have access to this model. "
            "Try a different model or check your API key permissions."
        )

    # Model not found
    if "NOT_FOUND" in msg or "404" in msg:
        return (
            "❓ **Model not found.**\n\n"
            "The selected Gemini model doesn't exist or isn't available. "
            "Try switching to `gemini-2.0-flash` in ⚙️ Settings."
        )

    # Fallback
    return f"**Gemini API error:** {msg}"


class GeminiProvider:
    """Chat provider backed by Google Gemini (google-genai SDK)."""

    def __init__(self, api_key: str, model: str):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model

    def stream_chat(self, messages: list, context: str) -> Iterator[str]:
        if not messages:
            return

        system_instruction = _SYSTEM_TEMPLATE.format(context=context)

        # Convert OpenAI-style history to Gemini Content objects
        # All but last message → history; last message → current turn
        history = []
        for msg in messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            history.append(
                types.Content(role=role, parts=[types.Part(text=msg["content"])])
            )

        # Build the config with system instruction
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
        )

        # Use chats for multi-turn with history
        chat = self.client.chats.create(
            model=self.model_name,
            config=config,
            history=history,
        )

        # Stream the response to the latest user message
        try:
            for chunk in chat.send_message_stream(messages[-1]["content"]):
                if chunk.text:
                    yield chunk.text
        except genai_errors.APIError as exc:
            raise RuntimeError(_friendly_gemini_error(exc)) from exc
