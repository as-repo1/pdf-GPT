"""
Embeddings layer — local sentence-transformers (default, no API key needed)
or OpenAI embeddings (optional).

Critical: SentenceTransformerEmbeddings inherits from LangchainEmbeddings so
FAISS correctly resolves embed_query instead of storing the object as a callable.
Also implements __call__ for older FAISS compat as a safety net.
"""

from typing import List

import streamlit as st

try:
    from langchain_core.embeddings import Embeddings as _LangchainBase
except ImportError:
    _LangchainBase = object  # graceful fallback


class SentenceTransformerEmbeddings(_LangchainBase):
    """
    Wrapper around sentence-transformers that is fully compatible with
    LangChain's FAISS vector store (both old and new versions).

    - Inherits LangchainEmbeddings → FAISS uses .embed_query correctly
    - Implements __call__          → works even if FAISS stores the object itself
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer  # pylint: disable=import-outside-toplevel
        self._model = SentenceTransformer(model_name)
        self._model_name = model_name

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        vecs = self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=32,
        )
        return vecs.tolist()

    def embed_query(self, text: str) -> List[float]:
        vec = self._model.encode(
            [text],
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vec[0].tolist()

    def __call__(self, text: str) -> List[float]:
        """
        Fallback: some FAISS versions store the embeddings object as
        embedding_function and call it directly. This makes that work.
        """
        return self.embed_query(text)


@st.cache_resource(show_spinner=False)
def _local_embeddings(model_name: str) -> SentenceTransformerEmbeddings:
    """Load and cache the sentence-transformer model (once per model name)."""
    return SentenceTransformerEmbeddings(model_name)


def get_embeddings(
    provider: str = "local",
    openai_api_key: str = "",
    openai_base_url: str = "",
    local_model: str = "all-MiniLM-L6-v2",
    openai_embedding_model: str = "text-embedding-3-small",
):
    """
    Return the appropriate embeddings object.

    provider='local'  → sentence-transformers (offline, no API key)
    provider='openai' → OpenAI embeddings (requires key)
    """
    if provider == "openai" and openai_api_key.strip():
        from langchain_openai import OpenAIEmbeddings  # pylint: disable=import-outside-toplevel
        return OpenAIEmbeddings(
            api_key=openai_api_key,
            base_url=openai_base_url or None,
            model=openai_embedding_model,
        )
    return _local_embeddings(local_model)


def create_vector_store(chunks: List[str], embeddings):
    """Build a FAISS in-memory vector store from text chunks."""
    from langchain_community.vectorstores import FAISS  # pylint: disable=import-outside-toplevel
    return FAISS.from_texts(chunks, embeddings)
