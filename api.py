import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any
import requests

from config import load_config, save_config, DEFAULT_CONFIG
from core.pdf_processor import extract_text_from_pdfs, split_text
from core.embeddings import create_vector_store, get_embeddings
from core.chat_engine import get_context

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Providers
from providers.openai_provider import OpenAIProvider
from providers.gemini_provider import GeminiProvider
from providers.ollama_provider import OllamaProvider

app = FastAPI(title="pdf-GPT API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes below
# But wait, we mount static files at the end so it doesn't override API routes.

# Global State for simplicity
global_vector_store = None
global_pdf_names = []

class ConfigUpdate(BaseModel):
    config: Dict[str, Any]

class ChatRequest(BaseModel):
    prompt: str
    messages: List[Dict[str, str]]

@app.get("/api/config")
def get_config():
    return load_config()

@app.post("/api/config")
def update_config(update: ConfigUpdate):
    save_config(update.config)
    return {"status": "success"}

@app.get("/api/models")
def get_models(provider: str, base_url: str = "", api_key: str = ""):
    if provider == "ollama":
        try:
            r = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=4)
            r.raise_for_status()
            return sorted(m["name"] for m in r.json().get("models", []))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    elif provider == "openai" or provider == "openrouter":
        if not api_key:
            return []
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=base_url or None)
            data = client.models.list().data
            return sorted(m.id for m in data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    return []

@app.post("/api/upload")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    global global_vector_store
    global global_pdf_names
    
    cfg = load_config()
    
    class FakeFile:
        def __init__(self, name, content):
            self.name = name
            self.content = content
        def getvalue(self):
            return self.content
            
    pdf_files = []
    pdf_names = []
    for file in files:
        content = await file.read()
        
        # Save to disk for frontend viewing
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(content)
            
        pdf_files.append(FakeFile(file.filename, content))
        pdf_names.append(file.filename)
        
    try:
        raw_text = extract_text_from_pdfs(pdf_files)
        chunks = split_text(raw_text, cfg.get("chunk_size", 1000), cfg.get("chunk_overlap", 200))
        emb = get_embeddings(
            provider=cfg["embedding_provider"],
            openai_api_key=cfg["openai"]["api_key"],
            openai_base_url=cfg["openai"]["base_url"],
            local_model=cfg.get("local_embedding_model", "all-MiniLM-L6-v2"),
            openai_embedding_model=cfg.get("openai_embedding_model", "text-embedding-3-small"),
        )
        global_vector_store = create_vector_store(chunks, emb)
        global_pdf_names = pdf_names
        return {"status": "success", "chunks": len(chunks), "files": len(pdf_files)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents")
def get_documents():
    global global_pdf_names
    return {"pdf_names": global_pdf_names}

@app.post("/api/clear")
def clear_documents():
    global global_vector_store
    global global_pdf_names
    global_vector_store = None
    global_pdf_names = []
    
    # Clear physical files
    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            pass
            
    return {"status": "success"}

def _build_provider(config: dict):
    provider_name = config["active_provider"]
    if provider_name == "openai":
        if not config["openai"]["api_key"].strip():
            raise ValueError("OpenAI API key is not set.")
        return OpenAIProvider(
            config["openai"]["api_key"],
            config["openai"]["base_url"],
            config["openai"]["model"],
        )
    elif provider_name == "gemini":
        if not config["gemini"]["api_key"].strip():
            raise ValueError("Gemini API key is not set.")
        return GeminiProvider(config["gemini"]["api_key"], config["gemini"]["model"])
    elif provider_name == "ollama":
        return OllamaProvider(config["ollama"]["base_url"], config["ollama"]["model"])
    elif provider_name == "openrouter":
        if not config["openrouter"]["api_key"].strip():
            raise ValueError("OpenRouter API key is not set.")
        return OpenAIProvider(
            config["openrouter"]["api_key"],
            config["openrouter"]["base_url"],
            config["openrouter"]["model"],
        )
    raise ValueError(f"Unknown provider: {provider_name}")

@app.post("/api/chat")
async def chat(req: ChatRequest):
    global global_vector_store
    if global_vector_store is None:
        raise HTTPException(status_code=400, detail="No documents uploaded.")
        
    cfg = load_config()
    try:
        provider = _build_provider(cfg)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    doc_context = get_context(global_vector_store, req.prompt, cfg.get("top_k", 4))
    
    def generate():
        try:
            for chunk in provider.stream_chat(req.messages, doc_context):
                yield chunk
        except Exception as e:
            yield f"\n\n**Error during generation:** {str(e)}"
            
    return StreamingResponse(generate(), media_type="text/plain")

# Mount uploads for PDF viewer
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Mount static files at the end so it acts as a fallback for the UI
app.mount("/", StaticFiles(directory="static", html=True), name="static")
