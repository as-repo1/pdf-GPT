"""
Ollama provider — connects to a local Ollama instance via its REST API.
No API key required. Supports any model installed via `ollama pull`.
"""

import json
from typing import Iterator

import requests

_SYSTEM_TEMPLATE = (
    "You are a helpful AI assistant specialized in analyzing PDF documents. "
    "Answer the user's question using ONLY the context excerpts below. "
    "If the answer is not present in the context, say so clearly and honestly. "
    "Be concise, accurate, and cite relevant parts when helpful.\n\n"
    "--- Document Context ---\n{context}\n--- End Context ---"
)


class OllamaProvider:
    """Chat provider backed by a local Ollama instance."""

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def stream_chat(self, messages: list, context: str) -> Iterator[str]:
        system_msg = {"role": "system", "content": _SYSTEM_TEMPLATE.format(context=context)}
        payload = {
            "model": self.model,
            "messages": [system_msg] + messages,
            "stream": True,
        }

        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                stream=True,
                timeout=120,
            )
            resp.raise_for_status()

            for line in resp.iter_lines():
                if not line:
                    continue
                data = json.loads(line)
                if data.get("done"):
                    break
                content = data.get("message", {}).get("content", "")
                if content:
                    yield content

        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Cannot reach Ollama at **{self.base_url}**.\n"
                "Make sure Ollama is running: `ollama serve`"
            )
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"Ollama API error: {e}")
