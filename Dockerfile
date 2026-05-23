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

# Streamlit config — disable telemetry and set sensible defaults
RUN mkdir -p /root/.streamlit && cat > /root/.streamlit/config.toml <<'EOF'
[browser]
gatherUsageStats = false

[server]
headless = true
port = 8501
address = "0.0.0.0"
enableCORS = false
enableXsrfProtection = false
# Stops Streamlit scanning all imported modules (prevents transformers noise)
fileWatcherType = "none"

[theme]
base = "dark"
EOF

# Config persistence: mount ~/.pdf-gpt-config.json here
VOLUME ["/root"]

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

ENTRYPOINT ["streamlit", "run", "app.py"]
