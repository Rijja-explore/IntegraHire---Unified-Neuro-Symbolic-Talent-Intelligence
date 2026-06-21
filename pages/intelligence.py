"""Candidate intelligence page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.dna_chart import render_dna_chart
from components.score_cards import render_score_cards
from utils.charts import timeline


def _candidate_dna(row: pd.Series) -> dict[str, float]:
    base = float(row.get("score", 0.0)) * 100
    return {
        "Technical Depth": min(100, max(0, base * 0.92)),
        "Authenticity": float(row.get("authenticity", 55)),
        "Production Readiness": float(row.get("production", 55)),
        "Career Stability": float(row.get("trajectory", 62)),
        "Behavior Reliability": float(row.get("behavior", 55)),
        "Learning Velocity": min(100, max(0, base * 0.84)),
        "Research Orientation": min(100, max(0, base * 0.76)),
        "Startup Fit": min(100, max(0, base * 0.88)),
    }


def render(data: dict) -> None:
    merged: pd.DataFrame = data["merged"].copy()
    st.markdown('<div class="ih-title">Candidate Intelligence</div>', unsafe_allow_html=True)

    if merged.empty:
        st.warning("No candidate data available.")
        return

    candidate_ids = merged["candidate_id"].astype(str).tolist()
    selected = st.selectbox("Select Candidate", candidate_ids)
    row = merged[merged["candidate_id"].astype(str) == selected].iloc[0]

    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown('<div class="ih-card">', unsafe_allow_html=True)
        st.subheader("Candidate Summary")
        st.write(f"Candidate ID: {row.get('candidate_id', '')}")
        st.write(f"Current Role: {row.get('role', 'Unknown')}")
        st.write(f"Experience: {row.get('experience', 0)} years")
        st.write(f"Location: {row.get('location', 'Unknown')}")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        render_dna_chart(_candidate_dna(row), title="Candidate DNA")

    score_cards = {
        "Semantic Score": float(row.get("score", 0.0)) * 100,
        "Authenticity Score": float(row.get("authenticity", 0.0)),
        "Trajectory Score": float(row.get("trajectory", 0.0)),
        "Production Score": float(row.get("production", 0.0)),
        "Behavior Score": float(row.get("behavior", 0.0)),
        "Final Score": float(row.get("score", 0.0)) * 100,
    }
    render_score_cards(score_cards)

    companies = ["Company A", "Company B", "Company C", "Current"]
    durations = [18, 26, 14, 22]
    st.plotly_chart(timeline(companies, durations), use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown('<div class="ih-card">', unsafe_allow_html=True)
        st.subheader("Top Strengths")
        for x in [
            "Strong retrieval systems experience",
            "Excellent recruiter engagement",
            "Consistent AI specialization",
        ]:
            st.write(f"- {x}")
        st.markdown("</div>", unsafe_allow_html=True)

    with c4:
        st.markdown('<div class="ih-card">', unsafe_allow_html=True)
        st.subheader("Concerns")
        for x in [
            "Long notice period",
            "Limited deployment experience",
            "Low recent activity",
        ]:
            st.write(f"- {x}")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="ih-card">', unsafe_allow_html=True)
    st.subheader("Recruiter Explanation")
    st.write(row.get("reasoning", "Reasoning not available for this candidate."))
    st.markdown("</div>", unsafe_allow_html=True)
