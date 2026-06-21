"""Job Description page."""

from __future__ import annotations

import io
from collections import Counter

import streamlit as st

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None

try:
    import docx
except Exception:  # pragma: no cover
    docx = None

from utils.charts import radar_chart


def _extract_text(uploaded) -> str:
    name = uploaded.name.lower()
    if name.endswith(".txt"):
        return uploaded.getvalue().decode("utf-8", errors="ignore")
    if name.endswith(".pdf") and PdfReader is not None:
        reader = PdfReader(io.BytesIO(uploaded.getvalue()))
        return "\n".join([page.extract_text() or "" for page in reader.pages])
    if name.endswith(".docx") and docx is not None:
        document = docx.Document(io.BytesIO(uploaded.getvalue()))
        return "\n".join([p.text for p in document.paragraphs])
    return ""


def _extract_intent(text: str) -> dict:
    words = [w.strip('.,:;()[]{}').lower() for w in text.split() if len(w) > 2]
    counts = Counter(words)
    common = [w for w, _ in counts.most_common(20)]
    required = [w for w in common if w in {"python", "ml", "ai", "sql", "aws", "docker", "kubernetes", "llm", "retrieval"}][:8]
    preferred = [w for w in common if w in {"leadership", "mentoring", "communication", "startup", "research", "infra"}][:6]
    return {
        "required_skills": required,
        "preferred_skills": preferred,
        "years_experience": "5+ years" if "senior" in words else "3+ years",
        "domain_expertise": "AI/ML Platforms",
        "behavioral_requirements": ["Ownership", "Execution", "Collaboration"],
    }


def render(data: dict) -> None:
    st.markdown('<div class="ih-title">Job Description Intelligence</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload JD", type=["txt", "pdf", "docx"])
    default_text = ""
    try:
        with open("job_description.txt", "r", encoding="utf-8") as fh:
            default_text = fh.read()
    except OSError:
        default_text = ""

    jd_text = _extract_text(uploaded) if uploaded else default_text
    jd_text = st.text_area("JD Viewer", value=jd_text, height=260)

    if not jd_text.strip():
        st.info("Upload or paste a job description to extract hiring intent.")
        return

    intent = _extract_intent(jd_text)

    st.subheader("Hiring Intent Extraction")
    st.write("Required Skills")
    st.markdown("".join([f'<span class="ih-pill">{x}</span>' for x in intent["required_skills"]]), unsafe_allow_html=True)
    st.write("Preferred Skills")
    st.markdown("".join([f'<span class="ih-pill">{x}</span>' for x in intent["preferred_skills"]]), unsafe_allow_html=True)
    st.write(f"Years Experience: {intent['years_experience']}")
    st.write(f"Domain Expertise: {intent['domain_expertise']}")
    st.write("Behavioral Requirements")
    st.markdown("".join([f'<span class="ih-pill">{x}</span>' for x in intent["behavioral_requirements"]]), unsafe_allow_html=True)

    radar_labels = ["AI/ML", "Retrieval", "Infrastructure", "Research", "Leadership", "Startup Fit"]
    radar_values = [85, 80, 72, 64, 58, 76]
    st.plotly_chart(radar_chart(radar_labels, radar_values, "Hiring Intent Radar"), use_container_width=True)
