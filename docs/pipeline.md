# Data Pipeline

The pdf-GPT application relies on a robust Retrieval-Augmented Generation (RAG) data pipeline. This pipeline transforms raw PDF binaries into semantic vectors, and eventually into natural language answers.

## Stage 1: Ingestion & Extraction (`POST /api/upload`)
1. **File Upload**: Raw PDF binaries are received by FastAPI via `UploadFile`.
2. **Text Extraction**: The `pdf_processor.py` module reads the binaries (using libraries like PyPDF2 or pdfplumber) and extracts raw strings.
3. **Text Chunking**: Since LLMs have finite context windows, the raw text is passed to a `RecursiveCharacterTextSplitter`. This breaks the text into smaller, overlapping chunks (e.g., 1000 characters with a 200-character overlap) to preserve semantic boundaries like paragraphs and sentences.

## Stage 2: Embedding & Storage
1. **Embedding Generation**: The chunks are passed to an embedding model (e.g., `HuggingFaceEmbeddings` via sentence-transformers). This converts human-readable text into dense numerical vectors that represent the semantic meaning of the text.
2. **Vector Indexing**: The vectors, along with their original text chunks (metadata), are loaded into a **FAISS** (Facebook AI Similarity Search) index. This index is held in the memory of the FastAPI server for hyper-fast retrieval.

## Stage 3: Retrieval & Generation (`POST /api/chat`)
1. **Query Embedding**: When a user asks a question, the query itself is converted into a vector using the exact same embedding model.
2. **Similarity Search**: The FAISS index performs a cosine similarity search comparing the query vector against all document vectors, returning the top *K* most relevant chunks.
3. **Prompt Assembly**: The retrieved chunks are formatted into a unified "Context" block. This context, along with the user's original question and the chat history, is injected into a system prompt.
4. **LLM Inference**: The prompt is sent to the selected LLM Provider (OpenAI, Gemini, Ollama).
5. **Streaming Output**: The LLM streams its generated answer back to the FastAPI server, which proxies the stream back to the Streamlit frontend.
