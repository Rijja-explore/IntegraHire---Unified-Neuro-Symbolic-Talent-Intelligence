"""IntegraHire Streamlit application entrypoint."""

from __future__ import annotations

import streamlit as st

from pages import analytics, dashboard, discovery, intelligence, job_description, rankings
from utils.data_loader import load_default_datasets
from utils.theme import inject_theme


st.set_page_config(
    page_title="IntegraHire",
    page_icon="🧠",
    layout="wide",
)

inject_theme()

ranked_df, merged_df, candidates, top100 = load_default_datasets()

ctx = {
    "ranked": ranked_df,
    "merged": merged_df,
    "candidates": candidates,
    "top100": top100,
}

with st.sidebar:
    st.markdown("## IntegraHire")
    st.caption("Unified Neuro-Symbolic Talent Intelligence")
    section = st.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "📄 Job Description",
            "🔍 Candidate Discovery",
            "🧠 Candidate Intelligence",
            "📊 Rankings",
            "📈 Analytics",
            "⚙ Settings",
        ],
    )

if section == "🏠 Dashboard":
    dashboard.render(ctx)
elif section == "📄 Job Description":
    job_description.render(ctx)
elif section == "🔍 Candidate Discovery":
    discovery.render(ctx)
elif section == "🧠 Candidate Intelligence":
    intelligence.render(ctx)
elif section == "📊 Rankings":
    rankings.render(ctx)
elif section == "📈 Analytics":
    analytics.render(ctx)
else:
    st.markdown('<div class="ih-title">Settings</div>', unsafe_allow_html=True)
    st.markdown('<div class="ih-card">', unsafe_allow_html=True)
    st.write("Runtime profile: CPU-only")
    st.write("Network policy: offline ranking execution")
    st.write("Output policy: exactly top-100 records")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    '<div class="ih-footer">IntegraHire | Unified Neuro-Symbolic Talent Intelligence<br/>Authenticity-Aware Candidate Discovery and Ranking</div>',
    unsafe_allow_html=True,
)
