# ─── ui/preview.py ───────────────────────────────────────────────────────────
# Renders the question preview and PDF download section

import streamlit as st
from utils.pdf_generator import generate_pdf


def render_preview(config: dict, questions: dict):
    """Display the generated question paper preview and PDF download button."""

    st.divider()
    st.markdown("## 👁️ Preview")

    # ── Header card ──
    st.markdown(f"""
    <div style="background:#f8f9fa; border:1px solid #dee2e6; border-radius:8px; color:black;
                padding:20px; font-family:'Times New Roman', serif;">
        <h3 style="text-align:center; margin:0">{config['university'].upper()}</h3>
        <h4 style="text-align:center; margin:4px 0">Faculty of {config['faculty']}</h4>
        <hr style="border:2px solid black; margin:6px 0"/>
        <hr style="border:0.5px solid black; margin:2px 0 8px 0"/>
        <table width="100%">
            <tr>
                <td><b>Subject:</b> {config['subject']}</td>
                <td><b>Code:</b> {config['subject_code']}</td>
            </tr>
            <tr>
                <td><b>Semester:</b> {config['semester']}</td>
                <td><b>Exam:</b> {config['exam_type']}</td>
            </tr>
            <tr>
                <td><b>Duration:</b> {config['duration']} Hours</td>
                <td><b>Max Marks:</b> {config['total_marks']}</td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    # ── Tabs for each section ──
    tab_a, tab_b, tab_c = st.tabs(["📌 Section A", "📖 Section B", "📝 Section C"])

    with tab_a:
        st.markdown(
            f"**Short Answer Questions** – Attempt any {config['sec_a_attempt']} "
            f"out of {config['sec_a_count']} "
            f"[{config['sec_a_attempt']} × {config['sec_a_marks']} = "
            f"{config['sec_a_attempt'] * config['sec_a_marks']} Marks]"
        )
        for i, q in enumerate(questions.get("section_a", [])):
            st.markdown(f"**Q.{i+1}** {q['question']} &nbsp;&nbsp; *[{q['marks']} marks]*")

    with tab_b:
        st.markdown(
            f"**Medium Answer Questions** – Attempt any {config['sec_b_attempt']} "
            f"out of {config['sec_b_count']} "
            f"[{config['sec_b_attempt']} × {config['sec_b_marks']} = "
            f"{config['sec_b_attempt'] * config['sec_b_marks']} Marks]"
        )
        for i, q in enumerate(questions.get("section_b", [])):
            st.markdown(f"**Q.{i+1}** {q['question']} &nbsp;&nbsp; *[{q['marks']} marks]*")
            for sp in q.get("sub_parts", []):
                st.markdown(f"&nbsp;&nbsp;&nbsp;({sp['part']}) {sp['text']} [{sp.get('marks', '')} marks]")

    with tab_c:
        st.markdown(
            f"**Long Answer Questions** – Attempt any {config['sec_c_attempt']} "
            f"out of {config['sec_c_count']} "
            f"[{config['sec_c_attempt']} × {config['sec_c_marks']} = "
            f"{config['sec_c_attempt'] * config['sec_c_marks']} Marks]"
        )
        for i, q in enumerate(questions.get("section_c", [])):
            st.markdown(f"**Q.{i+1}** {q['question']} &nbsp;&nbsp; *[{q['marks']} marks]*")
            for sp in q.get("sub_parts", []):
                st.markdown(f"&nbsp;&nbsp;&nbsp;({sp['part']}) {sp['text']} [{sp.get('marks', '')} marks]")

    # ── PDF download ──
    st.divider()
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        if st.button("📄 Generate & Download PDF", use_container_width=True):
            with st.spinner("Creating PDF..."):
                pdf_bytes = generate_pdf(config, questions)
                filename  = (
                    f"{config['subject_code']}_"
                    f"{config['semester'].replace(' ', '_')}_QuestionPaper.pdf"
                )
                st.download_button(
                    label="⬇️ Download Question Paper PDF",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True,
                )
