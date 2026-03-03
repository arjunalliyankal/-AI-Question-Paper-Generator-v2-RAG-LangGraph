import os
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from config import APP_TITLE, APP_ICON, APP_LAYOUT
from ui.form import render_form
from ui.preview import render_preview
from utils.rag import build_vector_store
from utils.graph import run_rag_pipeline

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout=APP_LAYOUT)

# ─── Sidebar — API Key ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔑 Groq API Key")
    st.caption("Paste your key here.")

    user_key = st.text_input(
        "Groq API Key",
        value=os.environ.get("GROQ_API_KEY", ""),
        type="password",
        placeholder="gsk_…",
        label_visibility="collapsed",
    )

    if user_key:
        os.environ["GROQ_API_KEY"] = user_key
        st.success("✅ API key set for this session")
    elif os.environ.get("GROQ_API_KEY"):
        st.info("✅ Key loaded from `.env`")
    else:
        st.warning("⚠️ No API key — generation will fail")

    st.markdown("---")
    st.markdown(
        "Get your free key at [console.groq.com](https://console.groq.com)",
        unsafe_allow_html=False,
    )


st.markdown("""
<style>
    .main-title { font-size:2rem; font-weight:700; color:green; text-align:center; }
    .stButton > button { background-color:#16213e; color:white; border-radius:6px; }
    .rag-badge {
        display:inline-block; background:#d4edda; color:#155724;
        border:1px solid #c3e6cb; border-radius:12px;
        padding:2px 10px; font-size:0.8rem; font-weight:600;
    }
    .no-rag-badge {
        display:inline-block; background:#fff3cd; color:#856404;
        border:1px solid #ffc107; border-radius:12px;
        padding:2px 10px; font-size:0.8rem; font-weight:600;
    }
</style>
""", unsafe_allow_html=True)

# ─── Session State ────────────────────────────────────────────────────────────
for key in ("generated_paper", "vector_store", "pdf_name"):
    if key not in st.session_state:
        st.session_state[key] = None

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown(f'<p class="main-title">{APP_ICON} {APP_TITLE}</p>', unsafe_allow_html=True)
st.markdown(
    "Generate university-style question papers powered by "
    "**Groq LLaMA 3.3** · **LangGraph RAG pipeline** · **FAISS vector search**"
)

# RAG status badge
if st.session_state.vector_store:
    st.markdown(
        f'<span class="rag-badge">🔍 RAG ON — indexed: {st.session_state.pdf_name}</span>',
        unsafe_allow_html=True,
    )
else:
    st.markdown('<span class="no-rag-badge">📄 RAG OFF — no PDF indexed</span>', unsafe_allow_html=True)

st.divider()

# ─── Form ─────────────────────────────────────────────────────────────────────
config, pdf_bytes = render_form()

# ─── On Generate ──────────────────────────────────────────────────────────────
if config:

    # 1. Build / rebuild vector store if a new PDF was uploaded
    if pdf_bytes:
        with st.spinner("📚 Processing PDF....."):
            try:
                vs = build_vector_store(pdf_bytes)
                st.session_state.vector_store = vs
                st.session_state.pdf_name = "uploaded PDF"
                st.success(f"✅ Vector store ready — {len(vs.chunks)} chunks indexed.")
            except Exception as e:
                st.error(f"❌ Failed to process PDF: {e}")
                st.stop()
    else:
        # Clear stale vector store if no PDF this run
        st.session_state.vector_store = None
        st.session_state.pdf_name     = None

    # 2. Run LangGraph pipeline
    mode = "RAG + LangGraph" if st.session_state.vector_store else "LangGraph (no RAG)"
    with st.spinner(f"🤖 Running {mode} pipeline…"):
        try:
            questions = run_rag_pipeline(
                config       = config,
                vector_store = st.session_state.vector_store,
            )
            st.session_state.generated_paper = {"config": config, "questions": questions}
            st.success("✅ Question paper generated successfully!")
        except Exception as e:
            st.error(f"❌ Generation error: {e}")

# ─── Preview & Download ───────────────────────────────────────────────────────
if st.session_state.generated_paper:
    render_preview(
        st.session_state.generated_paper["config"],
        st.session_state.generated_paper["questions"],
    )
