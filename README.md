<div align="center">

```
██████╗ ██████╗ ███████╗      ██████╗ ██████╗ ████████╗
██╔══██╗██╔══██╗██╔════╝     ██╔════╝ ██╔══██╗╚══██╔══╝
██████╔╝██║  ██║█████╗       ██║  ███╗██████╔╝   ██║   
██╔═══╝ ██║  ██║██╔══╝       ██║   ██║██╔═══╝    ██║   
██║     ██████╔╝██║          ╚██████╔╝██║        ██║   
╚═╝     ╚═════╝ ╚═╝           ╚═════╝ ╚═╝        ╚═╝   
```

### Chat with any PDF using the AI model of your choice

<br/>

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.2+-1C3C3C?style=for-the-badge&logo=chainlink&logoColor=white)](https://langchain.com)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)

<br/>

> **Drop a PDF. Pick a model. Ask anything.**  
> Powered by RAG — your documents, your AI, your rules.

<br/>

[**⚡ Quick Start**](#-quick-start) · [**🐳 Docker**](#-docker) · [**🔌 Providers**](#-providers) · [**🧩 Embeddings**](#-embeddings) · [**📁 Structure**](#-project-structure)

<br/>

---

</div>

## 🌟 What is pdf-GPT?

**pdf-GPT** is an open-source, self-hostable PDF chat application built with **Retrieval-Augmented Generation (RAG)**. Upload one or more PDFs, pick your preferred AI provider, and get accurate, context-grounded answers — streamed word by word, right in your browser.

Everything is configurable from the **in-app Settings panel** — no `.env` files to edit, no code to touch.

<br/>

## ✨ Features at a Glance

<table>
<tr>
<td>

**🔌 Multi-Provider Support**
- OpenAI GPT-4o, GPT-4-turbo, and more
- Google Gemini 2.0 Flash / 1.5 Pro
- Local Ollama (llama3, mistral, phi3…)
- Any OpenAI-compatible API endpoint

</td>
<td>

**⚙️ Fully Configurable UI**
- In-app Settings panel — no file editing
- API keys, base URLs, model names
- Persistent across restarts
- Reset to defaults anytime

</td>
</tr>
<tr>
<td>

**🖥️ Offline-First Embeddings**
- Local sentence-transformers by default
- No API key needed for embeddings
- 5 embedding model options
- Optional OpenAI embeddings

</td>
<td>

**🐳 Docker Ready**
- Multi-stage optimised image
- `docker compose up` — that's it
- Optional bundled Ollama service
- Named volumes for persistence

</td>
</tr>
<tr>
<td>

**📚 Smart Document Handling**
- Multiple PDFs simultaneously
- Page-labelled context extraction
- Configurable chunk size & overlap
- FAISS vector store for fast retrieval

</td>
<td>

**⚡ Modern Experience**
- Streamed responses (all providers)
- Dark glassmorphism UI
- Smooth animations & micro-interactions
- Live Ollama model list from API

</td>
</tr>
</table>

<br/>

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- An API key **OR** [Ollama](https://ollama.com) installed locally

```bash
# 1 · Clone the repository
git clone https://github.com/as-repo1/pdf-GPT.git
cd pdf-GPT

# 2 · Install dependencies
pip install -r requirements.txt

# 3 · Launch
streamlit run app.py
```

Open **`http://localhost:8501`** → click **⚙️ Settings** → add your API key → upload a PDF → start asking.

<br/>

---

## 🐳 Docker

The fastest way to get running — no Python setup needed.

### Option A — Cloud providers (OpenAI / Gemini)

```bash
docker compose up --build
```

### Option B — Fully local stack (pdf-GPT + Ollama, zero cloud)

```bash
# Start pdf-GPT and Ollama together
docker compose --profile ollama up --build

# Pull a model (first time only — open a new terminal)
docker exec -it ollama ollama pull llama3
```

Open **`http://localhost:8501`** — your settings survive restarts via a named Docker volume.

### Pre-seed API keys via environment (optional)

```bash
# Copy the example and fill in your keys
cp .env.example .env
nano .env

# Then start normally
docker compose up
```

<details>
<summary><b>🎮 GPU acceleration for Ollama (NVIDIA)</b></summary>

Uncomment the `deploy` block in `docker-compose.yml`:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

Requires [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html).

</details>

<br/>

---

## 🔌 Providers

### 🟢 OpenAI

| Setting | Value |
|---|---|
| API Key | `sk-...` from [platform.openai.com](https://platform.openai.com/api-keys) |
| Base URL | `https://api.openai.com/v1` (default) |
| Models | `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `gpt-3.5-turbo` |

The **Base URL** field makes pdf-GPT compatible with **any OpenAI-compatible endpoint**:

```
LM Studio    →  http://localhost:1234/v1
Groq         →  https://api.groq.com/openai/v1
Together AI  →  https://api.together.xyz/v1
Perplexity   →  https://api.perplexity.ai
Ollama       →  http://localhost:11434/v1
```

---

### 🔵 Google Gemini

| Setting | Value |
|---|---|
| API Key | Free key from [aistudio.google.com](https://aistudio.google.com) |
| Models | `gemini-2.0-flash`, `gemini-1.5-flash`, `gemini-1.5-pro`, `gemini-1.0-pro` |

`gemini-2.0-flash` is recommended — fastest with a generous free tier.

---

### 🟡 Ollama (Local, No API Key)

```bash
# Install
curl -fsSL https://ollama.com/install.sh | sh

# Pull your preferred model
ollama pull llama3          # Meta LLaMA 3 · 8B · General purpose
ollama pull mistral         # Mistral 7B  · Fast & capable
ollama pull phi3            # Microsoft Phi-3 · Lightweight
ollama pull gemma3          # Google Gemma 3 · Efficient
ollama pull codellama       # Meta CodeLlama · Code-focused
ollama pull qwen2.5         # Alibaba Qwen 2.5 · Multilingual
```

pdf-GPT **auto-detects** all installed models and shows them in a dropdown. Hit **🔄** to refresh after pulling new models.

<br/>

---

## 🧩 Embeddings

Embeddings convert your PDF text into vectors for semantic search. pdf-GPT uses **local sentence-transformers by default** — no API key, no internet required.

### Local Models (offline)

| Model | Speed | Quality | Dimensions | Best For |
|---|---|---|---|---|
| `all-MiniLM-L6-v2` | ⚡⚡⚡ | ★★★☆ | 384 | General use (default) |
| `all-MiniLM-L12-v2` | ⚡⚡ | ★★★★ | 384 | Balanced |
| `all-mpnet-base-v2` | ⚡ | ★★★★★ | 768 | Best accuracy |
| `paraphrase-multilingual-MiniLM-L12-v2` | ⚡⚡ | ★★★☆ | 384 | Non-English PDFs |
| `multi-qa-MiniLM-L6-cos-v1` | ⚡⚡⚡ | ★★★★ | 384 | Q&A tasks |

### OpenAI Embeddings (cloud)

| Model | Dimensions | Cost |
|---|---|---|
| `text-embedding-3-small` | 1536 | Low |
| `text-embedding-3-large` | 3072 | Medium |
| `text-embedding-ada-002` | 1536 | Low (legacy) |

> **Note:** Changing the embedding model or chunk settings takes effect on the **next PDF upload** — the existing vector store is not rebuilt automatically.

<br/>

---

## ⚙️ Settings Reference

All settings live in the **⚙️ Settings** panel inside the app and are saved to `~/.pdf-gpt-config.json`.

| Setting | Default | Description |
|---|---|---|
| Active Provider | `openai` | LLM backend to use |
| API Key | _(empty)_ | Provider-specific key |
| Base URL | `https://api.openai.com/v1` | OpenAI endpoint (change for proxies) |
| Model | `gpt-4o` | Chat model name |
| Embedding Engine | `local` | `local` (offline) or `openai` |
| Local Embed Model | `all-MiniLM-L6-v2` | Which sentence-transformer to use |
| Chunk Size | `1000` | Characters per document chunk |
| Chunk Overlap | `200` | Overlap between adjacent chunks |
| Top-K Results | `4` | Chunks retrieved per query |

<br/>

---

## 📁 Project Structure

```
pdf-GPT/
│
├── 📄 app.py                      Main Streamlit application
├── 🔧 config.py                   Config persistence (load/save ~/.pdf-gpt-config.json)
├── 📦 requirements.txt
│
├── 🐳 Dockerfile                  Multi-stage optimised Docker image
├── 🐳 docker-compose.yml          App + optional Ollama service
├── 🐳 .dockerignore
├── 🔐 .env.example                Environment variable template
│
├── providers/
│   ├── openai_provider.py         OpenAI + any compatible endpoint (streaming)
│   ├── gemini_provider.py         Google Gemini via google-genai SDK (streaming)
│   └── ollama_provider.py         Local Ollama via REST API (streaming)
│
├── core/
│   ├── pdf_processor.py           Multi-PDF extraction + recursive chunking
│   ├── embeddings.py              Embeddings layer (local / OpenAI) + FAISS store
│   └── chat_engine.py             RAG context retrieval
│
└── ui/
    └── styles.css                 Dark glassmorphism theme (Inter font)
```

<br/>

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **UI Framework** | [Streamlit](https://streamlit.io) |
| **LLM — OpenAI** | [openai-python](https://github.com/openai/openai-python) |
| **LLM — Gemini** | [google-genai](https://github.com/googleapis/python-genai) |
| **LLM — Ollama** | REST API via `requests` |
| **Embeddings (local)** | [sentence-transformers](https://www.sbert.net) |
| **Embeddings (cloud)** | [langchain-openai](https://github.com/langchain-ai/langchain) |
| **Vector Store** | [FAISS](https://github.com/facebookresearch/faiss) via LangChain |
| **PDF Parsing** | [pypdf](https://github.com/py-pdf/pypdf) |
| **Text Splitting** | [langchain-text-splitters](https://github.com/langchain-ai/langchain) |
| **Containerisation** | Docker + Docker Compose |

<br/>

---

## 🔒 Security & Privacy

- **API keys** are stored only in `~/.pdf-gpt-config.json` on your machine — never committed to git
- **PDF content** is processed and stored in memory only — nothing is persisted to disk
- Only the **retrieved context chunks** (not the whole PDF) are sent to the AI provider
- Use **Ollama** for a fully local, air-gapped setup with zero data leaving your machine

<br/>

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

```bash
# Fork and clone
git clone https://github.com/as-repo1/pdf-GPT.git
cd pdf-GPT

# Install and run
pip install -r requirements.txt
streamlit run app.py
```

Please open an issue before submitting large pull requests.

<br/>

---

## 📄 License

Distributed under the **MIT License** — see [LICENSE](LICENSE) for details.

<br/>

---

<div align="center">

**Built with ❤️ using Streamlit · LangChain · sentence-transformers · FAISS**

⭐ **Star this repo if it helped you!** ⭐

</div>
