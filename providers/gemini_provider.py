"""
Google Gemini provider using the modern google-genai SDK.
Supports system instructions and streaming multi-turn conversations.
"""

from typing import Iterator

from google import genai
from google.genai import types

_SYSTEM_TEMPLATE = (
    "You are a helpful AI assistant specialized in analyzing PDF documents. "
    "Answer the user's question using ONLY the context excerpts below. "
    "If the answer is not present in the context, say so clearly and honestly. "
    "Be concise, accurate, and cite relevant parts when helpful.\n\n"
    "--- Document Context ---\n{context}\n--- End Context ---"
)


class GeminiProvider:
    """Chat provider backed by Google Gemini (google-genai SDK)."""

    def __init__(self, api_key: str, model: str):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model

    def stream_chat(self, messages: list, context: str) -> Iterator[str]:
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
        for chunk in chat.send_message_stream(messages[-1]["content"]):
            if chunk.text:
                yield chunk.text
