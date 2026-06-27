# ── Stage 1: dependency builder ───────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# System deps needed to compile some wheels (faiss, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --prefix=/install --no-cache-dir -r requirements.txt


# ── Stage 2: lean runtime image ───────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="pdf-GPT" \
      org.opencontainers.image.description="AI-powered PDF chat — OpenAI · Gemini · Ollama" \
      org.opencontainers.image.source="https://github.com/as-repo1/pdf-GPT"

# Copy installed packages from builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy application source
COPY . .

# No streamlit config needed for vanilla FastAPI


# Config persistence: mount ~/.pdf-gpt-config.json here
VOLUME ["/root"]

EXPOSE 1212

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:1212/api/config || exit 1

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "1212"]
