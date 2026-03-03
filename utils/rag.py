# ─── utils/rag.py ────────────────────────────────────────────────────────────
# PDF → text → chunks → FAISS vector store → retrieve relevant context

import re
import io
from typing import List

from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

from config import EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_CHUNKS


# ── Singleton embedding model (loaded once) ──────────────────────────────────
_embedder: SentenceTransformer | None = None

def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBEDDING_MODEL)
    return _embedder


# ── PDF text extraction ───────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract all text from a PDF given its raw bytes."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    return "\n\n".join(pages)


# ── Text chunking ─────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks."""
    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


# ── FAISS vector store ────────────────────────────────────────────────────────

class VectorStore:
    """In-memory FAISS vector store for document chunks."""

    def __init__(self, chunks: List[str]):
        self.chunks = chunks
        embedder = _get_embedder()
        embeddings = embedder.encode(chunks, show_progress_bar=False)
        embeddings = np.array(embeddings, dtype="float32")

        # Normalise for cosine similarity
        faiss.normalize_L2(embeddings)

        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)   # Inner product ≈ cosine after normalise
        self.index.add(embeddings)

    def retrieve(self, query: str, k: int = TOP_K_CHUNKS) -> List[str]:
        """Return the top-k most relevant chunks for a query."""
        embedder = _get_embedder()
        q_vec = embedder.encode([query], show_progress_bar=False)
        q_vec = np.array(q_vec, dtype="float32")
        faiss.normalize_L2(q_vec)

        k = min(k, len(self.chunks))
        _, indices = self.index.search(q_vec, k)
        return [self.chunks[i] for i in indices[0] if i < len(self.chunks)]


# ── Public builder ────────────────────────────────────────────────────────────

def build_vector_store(pdf_bytes: bytes) -> VectorStore:
    """Full pipeline: bytes → text → chunks → VectorStore."""
    text   = extract_text_from_pdf(pdf_bytes)
    chunks = chunk_text(text)
    return VectorStore(chunks)
