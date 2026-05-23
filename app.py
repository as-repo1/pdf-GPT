"""
pdf-GPT  ·  Multi-provider PDF chat — OpenAI · Gemini · Ollama
"""

# ── Page config MUST be the very first Streamlit call ──────────────────────────
import streamlit as st

st.set_page_config(
    page_title="pdf-GPT",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ─────────────────────────────────────────────────────────────────────────
from pathlib import Path  # noqa: E402

_CSS = Path(__file__).parent / "ui" / "styles.css"
if _CSS.exists():
    st.markdown(f"<style>{_CSS.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ── Imports ──────────────────────────────────────────────────────────────────────
import requests  # noqa: E402

from config import DEFAULT_CONFIG, load_config, save_config  # noqa: E402
from core.chat_engine import get_context  # noqa: E402
from core.embeddings import create_vector_store, get_embeddings  # noqa: E402
from core.pdf_processor import extract_text_from_pdfs, split_text  # noqa: E402
from providers.gemini_provider import GeminiProvider  # noqa: E402
from providers.ollama_provider import OllamaProvider  # noqa: E402
from providers.openai_provider import OpenAIProvider  # noqa: E402


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

OPENAI_CHAT_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-16k",
]

GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
    "gemini-1.0-pro",
]

OPENAI_EMBED_MODELS = [
    "text-embedding-3-small",
    "text-embedding-3-large",
    "text-embedding-ada-002",
]

# name → (display label, description)
LOCAL_EMBED_MODELS = {
    "all-MiniLM-L6-v2": ("MiniLM-L6", "⚡ Fast · English · 384d  (default)"),
    "all-MiniLM-L12-v2": ("MiniLM-L12", "⚖️  Balanced · English · 384d"),
    "all-mpnet-base-v2": ("MPNet-base", "🎯 Best quality · English · 768d"),
    "paraphrase-multilingual-MiniLM-L12-v2": ("Multilingual-L12", "🌍 Multilingual · 384d"),
    "multi-qa-MiniLM-L6-cos-v1": ("QA-MiniLM", "🔍 Optimised for Q&A · 384d"),
}

OLLAMA_SUGGESTED = [
    "llama3", "llama3.1", "llama3.2",
    "mistral", "mistral-nemo",
    "phi3", "phi3.5",
    "gemma3", "gemma2",
    "codellama", "deepseek-coder",
    "qwen2.5",
]


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=30, show_spinner=False)
def _fetch_ollama_models(base_url: str):
    """Returns (model_list, error_code). Cached for 30 s."""
    try:
        r = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=4)
        r.raise_for_status()
        models = sorted(m["name"] for m in r.json().get("models", []))
        return models, None
    except requests.exceptions.ConnectionError:
        return [], "no_connection"
    except requests.exceptions.RequestException as exc:
        return [], str(exc)


@st.cache_data(ttl=60, show_spinner=False)
def _fetch_openai_models(api_key: str, base_url: str):
    """Try to list models from the OpenAI-compatible API. Returns list or []."""
    if not api_key.strip():
        return []
    try:
        from openai import OpenAI  # pylint: disable=import-outside-toplevel
        client = OpenAI(api_key=api_key, base_url=base_url or None)
        data = client.models.list().data
        return sorted(m.id for m in data)
    except (requests.exceptions.RequestException, RuntimeError, OSError):
        return []


def _init():
    defaults = {
        "config": load_config(),
        "messages": [],
        "vector_store": None,
        "pdf_names": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init()
cfg = st.session_state.config


_PROVIDER_BUILDERS = {
    "openai": lambda c: (
        (None, "OpenAI API key is not set — open ⚙️ Settings.")
        if not c["openai"]["api_key"].strip()
        else (
            OpenAIProvider(
                c["openai"]["api_key"],
                c["openai"]["base_url"],
                c["openai"]["model"],
            ),
            None,
        )
    ),
    "gemini": lambda c: (
        (None, "Gemini API key is not set — open ⚙️ Settings.")
        if not c["gemini"]["api_key"].strip()
        else (GeminiProvider(c["gemini"]["api_key"], c["gemini"]["model"]), None)
    ),
    "ollama": lambda c: (
        OllamaProvider(c["ollama"]["base_url"], c["ollama"]["model"]),
        None,
    ),
}


def build_provider(config: dict):
    """Instantiate the active LLM provider. Returns (provider, error_str)."""
    provider_name = config["active_provider"]
    builder = _PROVIDER_BUILDERS.get(provider_name)
    if builder is None:
        return None, f"Unknown provider: {provider_name}"
    try:
        return builder(config)
    except (ConnectionError, RuntimeError, OSError, ValueError) as exc:
        return None, str(exc)


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:

    # ── Brand ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="sidebar-brand">
        <span class="brand-icon">📄</span>
        <div>
            <div class="brand-title">pdf-GPT</div>
            <div class="brand-sub">AI Document Intelligence</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Provider status badge ─────────────────────────────────────────────────
    _PM = {
        "openai": ("#22c55e", "OpenAI"),
        "gemini": ("#3b82f6", "Gemini"),
        "ollama": ("#f59e0b", "Ollama"),
    }
    _p = cfg["active_provider"]
    _col, _lbl = _PM.get(_p, ("#888", _p.title()))
    _mdl = cfg[_p].get("model", "—")

    st.markdown(f"""
    <div class="provider-badge" style="border-color:{_col}33;background:{_col}11;">
        <div class="provider-dot" style="background:{_col};"></div>
        <span style="color:{_col};font-weight:600;">{_lbl}</span>
        <span class="model-chip">{_mdl}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Document upload ───────────────────────────────────────────────────────
    st.markdown('<div class="section-label">📂 Documents</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Upload PDFs", type="pdf",
        accept_multiple_files=True,
        label_visibility="collapsed",
        key="pdf_upload",
    )

    if uploaded:
        current_names = sorted(f.name for f in uploaded)
        if current_names != sorted(st.session_state.pdf_names):
            with st.spinner("Processing documents…"):
                try:
                    raw_text = extract_text_from_pdfs(uploaded)
                    chunks = split_text(raw_text, cfg["chunk_size"], cfg["chunk_overlap"])
                    emb = get_embeddings(
                        provider=cfg["embedding_provider"],
                        openai_api_key=cfg["openai"]["api_key"],
                        openai_base_url=cfg["openai"]["base_url"],
                        local_model=cfg.get("local_embedding_model", "all-MiniLM-L6-v2"),
                        openai_embedding_model=cfg.get(
                            "openai_embedding_model", "text-embedding-3-small"
                        ),
                    )
                    st.session_state.vector_store = create_vector_store(chunks, emb)
                    st.session_state.pdf_names = [f.name for f in uploaded]
                    st.session_state.messages = []
                    st.toast(
                        f"✓ {len(uploaded)} file(s) · {len(chunks)} chunks indexed",
                        icon="📄",
                    )
                except (OSError, RuntimeError, ValueError) as exc:
                    st.error(f"Processing failed: {exc}")

    if st.session_state.pdf_names:
        st.markdown('<div class="file-list">', unsafe_allow_html=True)
        for name in st.session_state.pdf_names:
            short = (name[:27] + "…") if len(name) > 30 else name
            st.markdown(f'<div class="file-item">📄 {short}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SETTINGS EXPANDER
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("⚙️  Settings", expanded=False):

        # ── Active provider ──────────────────────────────────────────────────
        st.markdown("#### 🔌 Provider")
        new_provider = st.selectbox(
            "provider",
            ["openai", "gemini", "ollama"],
            index=["openai", "gemini", "ollama"].index(cfg["active_provider"]),
            format_func=lambda x: {
                "openai": "🟢  OpenAI  (+ compatible APIs)",
                "gemini": "🔵  Google Gemini",
                "ollama": "🟡  Ollama  (local, no key)",
            }[x],
            label_visibility="collapsed",
            key="sel_provider",
        )
        cfg["active_provider"] = new_provider

        st.markdown("")

        # ── OpenAI ───────────────────────────────────────────────────────────
        if new_provider == "openai":

            st.markdown("**🔑 API Key**")
            cfg["openai"]["api_key"] = st.text_input(
                "oai_key", value=cfg["openai"]["api_key"],
                type="password", label_visibility="collapsed",
                placeholder="sk-…", key="inp_oai_key",
            )

            st.markdown("**🌐 Base URL**")
            cfg["openai"]["base_url"] = st.text_input(
                "oai_url", value=cfg["openai"]["base_url"],
                label_visibility="collapsed", key="inp_oai_url",
                help="Change for LM Studio, Groq, Together AI, etc.",
            )

            # Model selector — fetch from API if possible, else curated list
            st.markdown("**🤖 Chat Model**")
            fetched_oai = _fetch_openai_models(
                cfg["openai"]["api_key"], cfg["openai"]["base_url"]
            )
            oai_models = fetched_oai if fetched_oai else OPENAI_CHAT_MODELS
            # Keep custom model in list if user typed something non-standard
            cur_oai = cfg["openai"]["model"]
            if cur_oai and cur_oai not in oai_models:
                oai_models = [cur_oai] + oai_models

            oai_model_idx = (
                oai_models.index(cfg["openai"]["model"])
                if cfg["openai"]["model"] in oai_models
                else 0
            )
            cfg["openai"]["model"] = st.selectbox(
                "oai_model", oai_models,
                index=oai_model_idx,
                label_visibility="collapsed", key="sel_oai_model",
            )
            if not fetched_oai:
                st.caption("💡 Add your API key above to fetch available models automatically.")

        # ── Gemini ───────────────────────────────────────────────────────────
        elif new_provider == "gemini":

            st.markdown("**🔑 API Key**")
            cfg["gemini"]["api_key"] = st.text_input(
                "gem_key", value=cfg["gemini"]["api_key"],
                type="password", label_visibility="collapsed",
                placeholder="AIza…", key="inp_gem_key",
            )
            st.caption("Get a free key → [aistudio.google.com](https://aistudio.google.com)")

            st.markdown("**🤖 Chat Model**")
            cur_gem = cfg["gemini"]["model"]
            gem_list = GEMINI_MODELS if cur_gem in GEMINI_MODELS else [cur_gem] + GEMINI_MODELS
            cfg["gemini"]["model"] = st.selectbox(
                "gem_model", gem_list,
                index=gem_list.index(cfg["gemini"]["model"]),
                label_visibility="collapsed", key="sel_gem_model",
            )

        # ── Ollama ───────────────────────────────────────────────────────────
        elif new_provider == "ollama":

            st.markdown("**🌐 Ollama Host URL**")
            cfg["ollama"]["base_url"] = st.text_input(
                "ollama_url", value=cfg["ollama"]["base_url"],
                label_visibility="collapsed", key="inp_ollama_url",
            )

            st.markdown("**🤖 Chat Model**")
            col_mdl, col_ref = st.columns([5, 1])

            with col_ref:
                if st.button("🔄", key="btn_refresh_ollama",
                             help="Refresh model list from Ollama"):
                    _fetch_ollama_models.clear()
                    st.rerun()

            avail_models, ollama_err = _fetch_ollama_models(cfg["ollama"]["base_url"])

            if ollama_err == "no_connection":
                st.warning("⚠️ Cannot reach Ollama. Is it running?")
                st.markdown("""
                <div class="suggest-box">
                    <div class="suggest-title">▶ Start Ollama</div>
                    <code>ollama serve</code><br>
                    <div class="suggest-title" style="margin-top:8px;">💡 Popular models</div>
                    <code>ollama pull llama3</code><br>
                    <code>ollama pull mistral</code><br>
                    <code>ollama pull phi3</code><br>
                    <code>ollama pull gemma3</code>
                </div>
                """, unsafe_allow_html=True)
                with col_mdl:
                    cfg["ollama"]["model"] = st.text_input(
                        "ollama_model_txt", value=cfg["ollama"]["model"],
                        label_visibility="collapsed", key="inp_ollama_model_txt",
                        placeholder="llama3",
                    )

            elif not avail_models:
                st.info("🔌 Ollama is running but has no models installed.")
                st.markdown("""
                <div class="suggest-box">
                    <div class="suggest-title">Pull a model to get started</div>
                    <code>ollama pull llama3</code><br>
                    <code>ollama pull mistral</code><br>
                    <code>ollama pull phi3</code>
                </div>
                """, unsafe_allow_html=True)
                with col_mdl:
                    cfg["ollama"]["model"] = st.text_input(
                        "ollama_model_txt", value=cfg["ollama"]["model"],
                        label_visibility="collapsed", key="inp_ollama_model_empty",
                        placeholder="llama3",
                    )

            else:
                cur_oll = cfg["ollama"]["model"]
                if cur_oll in avail_models:
                    oll_list = avail_models
                elif cur_oll:
                    oll_list = [cur_oll] + avail_models
                else:
                    oll_list = avail_models
                oll_idx = (
                    oll_list.index(cfg["ollama"]["model"])
                    if cfg["ollama"]["model"] in oll_list
                    else 0
                )
                with col_mdl:
                    cfg["ollama"]["model"] = st.selectbox(
                        "ollama_model_sel", oll_list,
                        index=oll_idx,
                        label_visibility="collapsed", key="sel_ollama_model",
                    )
                st.caption(f"✅ {len(avail_models)} model(s) available")

        # ══════════════════════════════════════════════════════════════════════
        # EMBEDDINGS SECTION
        # ══════════════════════════════════════════════════════════════════════
        st.markdown("---")
        st.markdown("#### 🧩 Embeddings")

        cfg["embedding_provider"] = st.selectbox(
            "embed_prov",
            ["local", "openai"],
            index=0 if cfg["embedding_provider"] == "local" else 1,
            format_func=lambda x: (
                "🖥️  Local — sentence-transformers"
                if x == "local"
                else "☁️  OpenAI embeddings"
            ),
            label_visibility="collapsed", key="sel_embed",
            help="'Local' works fully offline with no API key.",
        )

        if cfg["embedding_provider"] == "local":
            st.markdown("**Embedding Model**")
            local_keys = list(LOCAL_EMBED_MODELS.keys())
            cur_local = cfg.get("local_embedding_model", "all-MiniLM-L6-v2")
            if cur_local not in local_keys:
                local_keys = [cur_local] + local_keys
            cfg["local_embedding_model"] = st.selectbox(
                "local_embed_model", local_keys,
                index=local_keys.index(cur_local),
                format_func=lambda k: (
                    f"{LOCAL_EMBED_MODELS.get(k, (k, ''))[0]}  —  "
                    f"{LOCAL_EMBED_MODELS.get(k, ('', k))[1]}"
                ),
                label_visibility="collapsed", key="sel_local_embed",
                help="First use downloads the model. Change takes effect on next upload.",
            )

        else:  # openai embeddings
            st.markdown("**Embedding Model**")
            cur_oai_emb = cfg.get("openai_embedding_model", "text-embedding-3-small")
            if cur_oai_emb in OPENAI_EMBED_MODELS:
                oai_emb_list = OPENAI_EMBED_MODELS
            else:
                oai_emb_list = [cur_oai_emb] + OPENAI_EMBED_MODELS
            cfg["openai_embedding_model"] = st.selectbox(
                "oai_embed_model", oai_emb_list,
                index=oai_emb_list.index(cur_oai_emb),
                label_visibility="collapsed", key="sel_oai_embed",
            )
            if not cfg["openai"]["api_key"].strip():
                st.warning("⚠️ Needs an OpenAI API key (set above).")

        # ══════════════════════════════════════════════════════════════════════
        # CHUNKING / RAG
        # ══════════════════════════════════════════════════════════════════════
        st.markdown("---")
        st.markdown("#### 📄 Chunking & Retrieval")

        st.markdown("**Chunk Size**")
        cfg["chunk_size"] = st.slider(
            "chunk_size", 300, 3000, cfg["chunk_size"], 100,
            label_visibility="collapsed",
            help="Larger = more context per chunk. Takes effect on next upload.",
        )

        st.markdown("**Chunk Overlap**")
        cfg["chunk_overlap"] = st.slider(
            "chunk_overlap", 0, 600, cfg["chunk_overlap"], 50,
            label_visibility="collapsed",
        )

        st.markdown("**Top-K Results**")
        cfg["top_k"] = st.slider(
            "top_k", 1, 12, cfg["top_k"],
            label_visibility="collapsed",
            help="Number of chunks retrieved per query.",
        )

        st.markdown("")
        col_s, col_r = st.columns(2)
        with col_s:
            if st.button("💾  Save", use_container_width=True, key="btn_save"):
                save_config(cfg)
                st.toast("Settings saved!", icon="✅")
        with col_r:
            if st.button("↩️  Reset", use_container_width=True, key="btn_reset"):
                st.session_state.config = {
                    k: v.copy() if isinstance(v, dict) else v
                    for k, v in DEFAULT_CONFIG.items()
                }
                save_config(st.session_state.config)
                st.rerun()

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    if st.button("🗑️  Clear Chat", use_container_width=True, key="btn_clear"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("""
    <div style="margin-top:auto;padding-top:16px;text-align:center;">
        <p style="font-size:0.7rem;color:#55557a;">pdf-GPT · open source</p>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT AREA
# ══════════════════════════════════════════════════════════════════════════════
cfg = st.session_state.config

st.markdown("""
<div class="app-header">
    <h1 class="app-title">pdf-<span class="accent">GPT</span></h1>
    <p class="app-subtitle">Upload a PDF · Pick a provider · Start asking questions</p>
</div>
""", unsafe_allow_html=True)

# ── Empty state ───────────────────────────────────────────────────────────────
if not st.session_state.vector_store:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">📄</div>
        <h3>Drop your PDF in the sidebar to begin</h3>
        <p>Documents are processed locally — only your questions and retrieved context
           are sent to the AI provider.</p>
        <div class="feature-grid">
            <div class="feature-card"><span>🔌</span><span>OpenAI · Gemini · Ollama</span></div>
            <div class="feature-card"><span>⚡</span><span>Streamed responses</span></div>
            <div class="feature-card"><span>🖥️</span><span>Local embeddings</span></div>
            <div class="feature-card"><span>📚</span><span>Multi-PDF support</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Chat interface ────────────────────────────────────────────────────────────
else:
    for msg in st.session_state.messages:
        avatar = "🧑" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask anything about your documents…", key="chat_input"):

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)

        provider, err = build_provider(cfg)

        if err:
            with st.chat_message("assistant", avatar="🤖"):
                st.error(f"⚠️ {err}")
        else:
            with st.chat_message("assistant", avatar="🤖"):
                doc_context = get_context(
                    st.session_state.vector_store, prompt, cfg["top_k"]
                )
                try:
                    full: str = st.write_stream(
                        provider.stream_chat(st.session_state.messages, doc_context)
                    )
                    st.session_state.messages.append(
                        {"role": "assistant", "content": full}
                    )
                except (ConnectionError, RuntimeError, OSError) as exc:
                    st.error(f"**Error:** {exc}")
