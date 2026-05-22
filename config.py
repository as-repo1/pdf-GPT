"""
Config management for pdf-GPT.
Settings are persisted to ~/.pdf-gpt-config.json and deep-merged with defaults
so new keys are always available even when upgrading from an older config.
"""

import json
from pathlib import Path
from typing import Any, Dict

CONFIG_FILE = Path.home() / ".pdf-gpt-config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "active_provider": "openai",
    "openai": {
        "api_key": "",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o",
    },
    "gemini": {
        "api_key": "",
        "model": "gemini-2.0-flash",
    },
    "ollama": {
        "base_url": "http://localhost:11434",
        "model": "llama3",
    },
    # Embedding settings
    "embedding_provider": "local",          # "local" or "openai"
    "local_embedding_model": "all-MiniLM-L6-v2",
    "openai_embedding_model": "text-embedding-3-small",
    # RAG settings
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "top_k": 4,
}


def _deep_copy_defaults() -> Dict[str, Any]:
    return {
        k: v.copy() if isinstance(v, dict) else v
        for k, v in DEFAULT_CONFIG.items()
    }


def load_config() -> Dict[str, Any]:
    """Load config from disk, deep-merging with defaults for any missing keys."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                saved = json.load(f)
            config = _deep_copy_defaults()
            for key, val in saved.items():
                if (
                    isinstance(val, dict)
                    and key in config
                    and isinstance(config[key], dict)
                ):
                    config[key].update(val)
                else:
                    config[key] = val
            return config
        except Exception:
            pass
    return _deep_copy_defaults()


def save_config(config: Dict[str, Any]) -> None:
    """Persist config to ~/.pdf-gpt-config.json."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
