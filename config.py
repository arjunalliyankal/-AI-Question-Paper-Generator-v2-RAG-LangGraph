# ─── config.py ───────────────────────────────────────────────────────────────
import os

# ── Groq / LLM ──
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = "llama-3.3-70b-versatile"
MAX_TOKENS   = 4000

# ── Embeddings (free, local, no API key needed) ──
EMBEDDING_MODEL = "all-MiniLM-L6-v2"   # sentence-transformers model

# ── RAG / chunking ──
CHUNK_SIZE    = 500    # characters per chunk
CHUNK_OVERLAP = 100
TOP_K_CHUNKS  = 8      # how many chunks to retrieve for context

# ── App ──
APP_TITLE  = "AI Question Paper Generator"
APP_ICON   = "📝"
APP_LAYOUT = "wide"

# ── Form defaults ──
DEFAULT_UNIVERSITY   = "University of Calicut"
DEFAULT_FACULTY      = "Computer Science"
DEFAULT_SUBJECT      = ""
DEFAULT_SUBJECT_CODE = "CS101"
DEFAULT_TOPICS = ""

EXAM_TYPES        = ["End Semester Examination (ESE)", "Mid Semester Examination (MSE)", "Internal Examination"]
DIFFICULTY_LEVELS = ["Easy", "Medium", "Hard", "Mixed"]
DURATIONS         = [1, 2, 3, 4]
SEMESTERS         = [f"Semester {i}" for i in range(1, 9)]
