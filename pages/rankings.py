"""Rankings page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.candidate_table import render_candidate_table
from components.dna_chart import render_dna_chart


def _dna_from_row(row: pd.Series) -> dict[str, float]:
    score = float(row.get("score", 0.0)) * 100
    return {
        "Technical Depth": min(100, score * 0.9),
        "Authenticity": float(row.get("authenticity", 50)),
        "Production": float(row.get("production", 50)),
        "Trajectory": float(row.get("trajectory", 50)),
        "Behavior": float(row.get("behavior", 50)),
        "Startup Fit": min(100, score * 0.85),
    }


def render(data: dict) -> None:
    ranked: pd.DataFrame = data["ranked"].copy()
    st.markdown('<div class="ih-title">Recruiter-Centric Rankings</div>', unsafe_allow_html=True)

    if ranked.empty:
        st.warning("No ranking output found. Generate test_submission.csv first.")
        return

    table_cols = [c for c in ["rank", "candidate_id", "score", "authenticity", "production", "behavior", "reasoning"] if c in ranked.columns]
    st.subheader("Top 100 Candidates")
    render_candidate_table(ranked[table_cols], key="rankings-table")

    st.subheader("Candidate Comparison")
    ids = ranked["candidate_id"].astype(str).tolist()
    c1, c2 = st.columns(2)
    with c1:
        cand_a = st.selectbox("Candidate A", ids, key="cand-a")
    with c2:
        cand_b = st.selectbox("Candidate B", ids, index=1 if len(ids) > 1 else 0, key="cand-b")

    row_a = ranked[ranked["candidate_id"].astype(str) == cand_a].iloc[0]
    row_b = ranked[ranked["candidate_id"].astype(str) == cand_b].iloc[0]

    c3, c4 = st.columns(2)
    with c3:
        st.markdown('<div class="ih-card">', unsafe_allow_html=True)
        st.write(f"A Rank: {row_a.get('rank', '-')}")
        st.write(f"A Final Score: {float(row_a.get('score', 0.0)):.4f}")
        st.write(f"A Trajectory: {float(row_a.get('trajectory', 0.0)):.2f}")
        st.write(f"A Behavior: {float(row_a.get('behavior', 0.0)):.2f}")
        st.markdown("</div>", unsafe_allow_html=True)
        render_dna_chart(_dna_from_row(row_a), "Candidate A DNA")

    with c4:
        st.markdown('<div class="ih-card">', unsafe_allow_html=True)
        st.write(f"B Rank: {row_b.get('rank', '-')}")
        st.write(f"B Final Score: {float(row_b.get('score', 0.0)):.4f}")
        st.write(f"B Trajectory: {float(row_b.get('trajectory', 0.0)):.2f}")
        st.write(f"B Behavior: {float(row_b.get('behavior', 0.0)):.2f}")
        st.markdown("</div>", unsafe_allow_html=True)
        render_dna_chart(_dna_from_row(row_b), "Candidate B DNA")
