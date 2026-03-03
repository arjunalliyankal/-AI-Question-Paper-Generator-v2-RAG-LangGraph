# 📝 AI Question Paper Generator v2 — RAG + LangGraph

Generates university-style question papers using **Groq LLaMA 3.3**, a **LangGraph** agentic pipeline, and optional **FAISS RAG** from an uploaded PDF.

## Project Structure

```
├── app.py                        ← Streamlit entry point
├── config.py                     ← All settings & constants
├── requirements.txt
├── utils/
│   ├── rag.py                    ← PDF extraction, chunking, FAISS vector store
│   ├── graph.py                  ← LangGraph StateGraph (4 nodes)
│   ├── pdf_generator.py          ← ReportLab PDF output
│   └── __init__.py
└── ui/
    ├── form.py                   ← Config form + PDF uploader
    ├── preview.py                ← Question preview + download
    └── __init__.py
```

## LangGraph Pipeline

```
[retrieve_context]          ← Query FAISS with topic keywords, get top-K chunks
        ↓
[build_prompt]              ← Inject RAG context block into the LLM prompt
        ↓
[generate_questions]        ← Call Groq LLaMA 3.3 70B, get JSON
        ↓
[parse_output]              ← Validate & parse JSON into section_a/b/c
        ↓
       END
```

When **no PDF is uploaded**, `retrieve_context` is skipped and the LLM generates from topic keywords alone.

## Setup

```bash
pip install -r requirements.txt

# Set your Groq API key
export GROQ_API_KEY="gsk_..."       # Mac/Linux
set GROQ_API_KEY=gsk_...            # Windows CMD

python -m streamlit run app.py
```

## How RAG Works

1. Upload any PDF (syllabus, textbook chapter, notes)
2. `pypdf` extracts the full text
3. Text is split into overlapping 500-char chunks
4. `sentence-transformers` (`all-MiniLM-L6-v2`) embeds all chunks locally (no API call)
5. Embeddings stored in a `faiss-cpu` index
6. At generation time, a query is built from your subject + topics
7. Top-8 most relevant chunks are retrieved and injected into the LLM prompt
8. Groq LLaMA generates questions grounded in your actual PDF content
