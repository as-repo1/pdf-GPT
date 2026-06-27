# Codebase Architecture

The **pdf-GPT** repository follows a Client-Server architecture, decoupled via RESTful HTTP APIs. 

## Directory Structure

```text
pdf-GPT/
├── api.py                 # The FastAPI backend entrypoint (Server & UI Server)
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker orchestrator for pdf-GPT and Ollama
├── Dockerfile             # Multi-stage Docker build
├── static/                # Vanilla HTML/JS/CSS frontend
│   ├── index.html
│   ├── style.css
│   └── script.js
├── docs/                  # Project documentation (this folder)
├── core/                  # Core RAG and Processing Logic
│   ├── chat_engine.py     
│   ├── embeddings.py      
│   └── pdf_processor.py   
└── providers/             # LLM API Adapters
    ├── openai_provider.py
    ├── gemini_provider.py
    └── ollama_provider.py
```

## Key Components

### 1. `api.py` (The Backend)
A FastAPI application running on port `1212`. It holds the state of the application (the FAISS vector store is maintained in memory as a global variable `GLOBAL_VECTOR_STORE`). It exposes standard REST endpoints (`/api/upload`, `/api/chat`, etc.) and mounts the `static/` directory to serve the frontend.

### 2. `static/` (The Frontend)
A lightweight vanilla HTML, CSS, and JS frontend. It maintains session state for the UI (chat history, selected provider) and communicates exclusively with `api.py` via the standard `fetch` API, rendering streaming responses dynamically.

### 3. `core/` (The Engine)
- **`pdf_processor.py`**: Handles binary file parsing and semantic chunking.
- **`embeddings.py`**: Wraps the initialization of `sentence-transformers` and the creation/updating of the FAISS index.
- **`chat_engine.py`**: The central orchestrator for a chat turn. It takes a query, fetches from FAISS, routes the request to the correct provider in `providers/`, and returns the streaming generator.

### 4. `providers/` (The Adapters)
A set of modules that normalize the disparate APIs of OpenAI, Gemini, and Ollama into a standard `stream_chat(prompt, history, api_key)` function signature.
