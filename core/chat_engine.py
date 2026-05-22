"""
RAG chat engine — retrieves relevant document context from the vector store
and passes it to the active provider for answering.
"""


def get_context(vector_store, query: str, top_k: int = 4) -> str:
    """
    Retrieve the top-k most semantically similar chunks for a query.
    Returns them joined with a separator for easy injection into prompts.
    """
    docs = vector_store.similarity_search(query, k=top_k)
    return "\n\n---\n\n".join(doc.page_content for doc in docs)
