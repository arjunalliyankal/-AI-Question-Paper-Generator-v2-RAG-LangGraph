# ─── utils/graph.py ──────────────────────────────────────────────────────────
# LangGraph RAG agent:
#
#   [retrieve_context] → [build_prompt] → [generate_questions] → [parse_output]
#
# Each node is a pure function; LangGraph wires them into a StateGraph.

import json
import re
from typing import TypedDict, Optional, List

from langgraph.graph import StateGraph, END
from groq import Groq

from config import GROQ_MODEL, MAX_TOKENS, TOP_K_CHUNKS
from utils.rag import VectorStore


# ─── Graph State ─────────────────────────────────────────────────────────────

class PaperState(TypedDict):
    config:       dict                  # paper configuration
    vector_store: Optional[VectorStore] # None when no PDF uploaded
    context:      str                   # retrieved RAG context
    prompt:       str                   # final prompt sent to LLM
    raw_response: str                   # raw LLM output
    questions:    dict                  # parsed JSON questions
    error:        Optional[str]


# ─── Node: retrieve_context ───────────────────────────────────────────────────

def retrieve_context(state: PaperState) -> PaperState:
    """
    If a vector store exists, retrieve relevant chunks using a query
    built from the paper config (subject + topics).
    """
    vs: Optional[VectorStore] = state.get("vector_store")
    if vs is None:
        return {**state, "context": ""}

    cfg   = state["config"]
    query = (
        f"{cfg['subject']} exam questions on "
        f"{', '.join(cfg['topics'][:5]) if cfg['topics'] else cfg['subject']}. "
        f"Difficulty: {cfg['difficulty']}."
    )
    chunks  = vs.retrieve(query, k=TOP_K_CHUNKS)
    context = "\n\n---\n\n".join(chunks)
    return {**state, "context": context}


# ─── Node: build_prompt ───────────────────────────────────────────────────────

def build_prompt(state: PaperState) -> PaperState:
    """Assemble the full LLM prompt, injecting RAG context when available."""
    cfg     = state["config"]
    context = state.get("context", "")

    rag_block = ""
    if context:
        rag_block = f"""
## Reference Material (extracted from uploaded PDF)
Use the content below as the primary source for generating questions.
Ensure questions reflect the topics, terminology, and depth found in this material.

<context>
{context}
</context>

"""

    prompt = f"""You are an expert university professor creating an exam question paper.
{rag_block}
Generate a complete question paper for:
- Subject: {cfg['subject']}
- Subject Code: {cfg['subject_code']}
- Semester: {cfg['semester']}
- Total Marks: {cfg['total_marks']}
- Duration: {cfg['duration']} Hours
- Exam Type: {cfg['exam_type']}
- Difficulty: {cfg['difficulty']}
- Topics to cover: {', '.join(cfg['topics']) if cfg['topics'] else 'General topics of the subject'}

The question paper MUST follow this EXACT structure:

SECTION A: Short Answer Questions
- {cfg['sec_a_count']} questions × {cfg['sec_a_marks']} marks
- Attempt any {cfg['sec_a_attempt']} out of {cfg['sec_a_count']}; section total = {cfg['sec_a_attempt'] * cfg['sec_a_marks']} marks
- 1–2 sentence answers

SECTION B: Medium Answer Questions
- {cfg['sec_b_count']} questions × {cfg['sec_b_marks']} marks = {cfg['sec_b_count'] * cfg['sec_b_marks']} marks
- Attempt any {cfg['sec_b_attempt']} out of {cfg['sec_b_count']}

SECTION C: Long Answer / Essay Questions
- {cfg['sec_c_count']} questions × {cfg['sec_c_marks']} marks = {cfg['sec_c_count'] * cfg['sec_c_marks']} marks
- Attempt any {cfg['sec_c_attempt']} out of {cfg['sec_c_count']}
- Include sub-parts (a), (b), (c) where applicable

Return ONLY a valid JSON object with this exact structure:
{{
  "section_a": [
    {{"q_no": 1, "question": "...", "marks": {cfg['sec_a_marks']}}},
    ...
  ],
  "section_b": [
    {{"q_no": 1, "question": "...", "marks": {cfg['sec_b_marks']}, "sub_parts": []}},
    ...
  ],
  "section_c": [
    {{"q_no": 1, "question": "...", "marks": {cfg['sec_c_marks']}, "sub_parts": [
      {{"part": "a", "text": "...", "marks": 5}},
      {{"part": "b", "text": "...", "marks": 5}}
    ]}},
    ...
  ]
}}"""

    return {**state, "prompt": prompt}


# ─── Node: generate_questions ────────────────────────────────────────────────

def generate_questions_node(state: PaperState) -> PaperState:
    """Call Groq LLM with the assembled prompt."""
    client = Groq()
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert university professor. "
                        "Always respond with valid JSON only — "
                        "no preamble, no markdown, no explanation."
                    ),
                },
                {"role": "user", "content": state["prompt"]},
            ],
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()
        return {**state, "raw_response": raw, "error": None}
    except Exception as e:
        return {**state, "raw_response": "", "error": str(e)}


# ─── Node: parse_output ──────────────────────────────────────────────────────

def parse_output(state: PaperState) -> PaperState:
    """Parse the raw LLM JSON response into a structured dict."""
    if state.get("error"):
        return state

    text = state["raw_response"]
    try:
        m = re.search(r'\{.*\}', text, re.DOTALL)
        questions = json.loads(m.group() if m else text)
        return {**state, "questions": questions}
    except Exception as e:
        return {**state, "questions": {}, "error": f"JSON parse error: {e}"}


# ─── Build the Graph ──────────────────────────────────────────────────────────

def build_graph():
    """Compile and return the LangGraph StateGraph."""
    graph = StateGraph(PaperState)

    graph.add_node("retrieve_context",     retrieve_context)
    graph.add_node("build_prompt",         build_prompt)
    graph.add_node("generate_questions",   generate_questions_node)
    graph.add_node("parse_output",         parse_output)

    graph.set_entry_point("retrieve_context")
    graph.add_edge("retrieve_context",   "build_prompt")
    graph.add_edge("build_prompt",       "generate_questions")
    graph.add_edge("generate_questions", "parse_output")
    graph.add_edge("parse_output",       END)

    return graph.compile()


# ─── Public API ───────────────────────────────────────────────────────────────

# Compiled graph — created once at import time
_compiled_graph = None

def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def run_rag_pipeline(config: dict, vector_store: Optional[VectorStore] = None) -> dict:
    """
    Run the full LangGraph RAG pipeline.

    Args:
        config:       Paper configuration dict.
        vector_store: Pre-built FAISS VectorStore, or None for no RAG.

    Returns:
        Generated questions dict (section_a, section_b, section_c).

    Raises:
        RuntimeError: if the graph returns an error.
    """
    initial_state: PaperState = {
        "config":       config,
        "vector_store": vector_store,
        "context":      "",
        "prompt":       "",
        "raw_response": "",
        "questions":    {},
        "error":        None,
    }

    graph  = get_graph()
    result = graph.invoke(initial_state)

    if result.get("error"):
        raise RuntimeError(result["error"])

    return result["questions"]
