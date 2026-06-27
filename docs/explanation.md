# Technical Explanation

This document explains the core theoretical concepts powering **pdf-GPT**.

## 1. Retrieval-Augmented Generation (RAG)
Large Language Models (LLMs) are trained on vast amounts of public data, but they do not know about your private documents, recent events, or highly specific proprietary information. If you ask an LLM about a specific internal PDF, it will either hallucinate an answer or state it doesn't know.

**RAG solves this by providing an open-book exam for the LLM.**
Instead of relying on the LLM's internal memory, we:
1. Search our documents for the answer first (Retrieval).
2. Append those relevant snippets to the prompt.
3. Ask the LLM to answer the question *strictly based on the provided snippets* (Generation).

## 2. Vector Embeddings
How do we know which parts of a 500-page PDF contain the answer to the user's question? Keyword search is too brittle (e.g., searching for "money" won't find paragraphs about "currency" or "capital").

We use **Embeddings**. Embeddings are high-dimensional vectors (lists of numbers) that represent the semantic meaning of text. In vector space, sentences with similar meanings are located physically close to each other. By mapping the user's question and all the paragraphs in the PDF into this same vector space, we can simply calculate the distance between them (Cosine Similarity) to find the most relevant paragraphs.

## 3. FAISS (Vector Database)
Comparing a question vector to millions of document vectors sequentially is computationally expensive. **FAISS** (Facebook AI Similarity Search) is a library that builds highly optimized indexes to perform these similarity searches in milliseconds, allowing the chat interface to feel snappy and responsive.

## 4. Provider Adapters
Different LLMs have different APIs. OpenAI uses one format, Google Gemini uses another, and Ollama uses a completely distinct local API. 
To abstract this complexity away from the core logic, pdf-GPT uses the **Adapter Pattern**. The `providers/` directory contains uniform wrappers around these different APIs, ensuring that the core `api.py` and `chat_engine.py` can treat all LLMs exactly the same way.
