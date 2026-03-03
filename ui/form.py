# ─── ui/form.py ──────────────────────────────────────────────────────────────
# Renders the configuration form + PDF upload; returns (config, pdf_bytes)

import streamlit as st
from config import (
    DEFAULT_UNIVERSITY, DEFAULT_FACULTY, DEFAULT_SUBJECT,
    DEFAULT_SUBJECT_CODE, DEFAULT_TOPICS,
    EXAM_TYPES, DIFFICULTY_LEVELS, DURATIONS, SEMESTERS,
)


def render_form():
    """
    Render the full input form with optional PDF upload.

    Returns:
        (config dict, pdf_bytes | None) when Generate is clicked,
        (None, None) otherwise.
    """

    # ── PDF Upload Banner ──────────────────────────────────────────────────────
    st.markdown("### 📄 Upload Reference PDF *(optional — enables RAG)*")
    st.markdown(
        "Upload your syllabus, textbook chapter, or notes. "
        "The AI will use the content to generate contextually relevant questions."
    )

    uploaded_file = st.file_uploader(
        "Drop a PDF here",
        type=["pdf"],
        help="The PDF will be chunked and indexed in a FAISS vector store for RAG.",
    )

    pdf_bytes = None
    if uploaded_file:
        pdf_bytes = uploaded_file.read()
        st.success(
            f"✅ **{uploaded_file.name}** uploaded — "
            f"{len(pdf_bytes) / 1024:.1f} KB · RAG mode **ON**"
        )
    else:
        st.info("No PDF uploaded — questions will be generated from topic keywords only.")

    st.divider()

    # ── Two-column config form ─────────────────────────────────────────────────
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 🏫 Institution Details")
        university = st.text_input("University Name", DEFAULT_UNIVERSITY)
        faculty    = st.text_input("Faculty / Department", DEFAULT_FACULTY)

        st.markdown("### 📚 Subject Details")
        subject      = st.text_input("Subject Name", DEFAULT_SUBJECT)
        subject_code = st.text_input("Subject Code", DEFAULT_SUBJECT_CODE)
        semester     = st.selectbox("Semester", SEMESTERS, index=0)
        exam_type    = st.selectbox("Exam Type", EXAM_TYPES)
        duration     = st.selectbox("Duration (Hours)", DURATIONS, index=2)
        difficulty   = st.selectbox("Difficulty Level", DIFFICULTY_LEVELS)

    with col2:
        st.markdown("### 📋 Topics to Cover")
        st.caption("These topics are used to generate questions.")
        topics_input = st.text_area(
            "Enter topics (one per line)",
            DEFAULT_TOPICS,
            height=150,
        )

        st.markdown("### 📊 Section Configuration")

        with st.expander("Section A – Short Answer", expanded=True):
            c1, c2, c3, c4 = st.columns(4)
            sec_a_count   = c1.number_input("Total Questions", 5, 20, 10, key="sa_count")
            sec_a_attempt = c2.number_input("Attempt Any",     1, 20, 10, key="sa_attempt")
            sec_a_marks   = c3.number_input("Marks Each",      1,  5,  2, key="sa_marks")
            c4.metric("Section Total", f"{sec_a_attempt * sec_a_marks}")

        with st.expander("Section B – Medium Answer", expanded=True):
            c1, c2, c3, c4 = st.columns(4)
            sec_b_count   = c1.number_input("Total Questions", 3, 10,  6, key="sb_count")
            sec_b_attempt = c2.number_input("Attempt Any",     1, 10,  4, key="sb_attempt")
            sec_b_marks   = c3.number_input("Marks Each",      5, 15, 10, key="sb_marks")
            c4.metric("Section Total", f"{sec_b_attempt * sec_b_marks}")

        with st.expander("Section C – Long Answer", expanded=True):
            c1, c2, c3, c4 = st.columns(4)
            sec_c_count   = c1.number_input("Total Questions",  2,  8,  4, key="sc_count")
            sec_c_attempt = c2.number_input("Attempt Any",      1,  8,  2, key="sc_attempt")
            sec_c_marks   = c3.number_input("Marks Each",      10, 30, 20, key="sc_marks")
            c4.metric("Section Total", f"{sec_c_attempt * sec_c_marks}")

        # Auto-computed total marks
        total_marks = (sec_a_attempt * sec_a_marks) + (sec_b_attempt * sec_b_marks) + (sec_c_attempt * sec_c_marks)
        st.metric("🧮 Total Marks (auto-computed)", f"{total_marks}")

    st.divider()

    # ── Generate button ────────────────────────────────────────────────────────
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        label   = "🚀 Generate with RAG" if pdf_bytes else "🚀 Generate Question Paper"
        clicked = st.button(label, use_container_width=True, type="primary")

    if clicked:
        config = {
            "university":    university,
            "faculty":       faculty,
            "subject":       subject,
            "subject_code":  subject_code,
            "semester":      semester,
            "exam_type":     exam_type,
            "duration":      duration,
            "total_marks":    total_marks,
            "difficulty":     difficulty,
            "topics":         [t.strip() for t in topics_input.strip().split("\n") if t.strip()],
            "sec_a_count":    sec_a_count,
            "sec_a_attempt":  sec_a_attempt,
            "sec_a_marks":    sec_a_marks,
            "sec_b_count":    sec_b_count,
            "sec_b_attempt":  sec_b_attempt,
            "sec_b_marks":    sec_b_marks,
            "sec_c_count":    sec_c_count,
            "sec_c_attempt":  sec_c_attempt,
            "sec_c_marks":    sec_c_marks,
        }
        return config, pdf_bytes

    return None, None
