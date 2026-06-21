"""Candidate discovery page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.candidate_table import render_candidate_table


def render(data: dict) -> None:
    merged: pd.DataFrame = data["merged"].copy()
    st.markdown('<div class="ih-title">Candidate Discovery</div>', unsafe_allow_html=True)

    if merged.empty:
        st.warning("No candidate data available.")
        return

    query = st.text_input("Semantic Search", placeholder="Try: retrieval engineer, LLM infra, ranking systems")

    c1, c2, c3 = st.columns(3)
    with c1:
        min_exp = st.slider("Experience", 0, 20, 0)
        min_auth = st.slider("Authenticity", 0, 100, 0)
    with c2:
        min_beh = st.slider("Behavior", 0, 100, 0)
        min_prod = st.slider("Production", 0, 100, 0)
    with c3:
        location = st.selectbox("Location", ["All"] + sorted([str(x) for x in merged["location"].dropna().unique()]))

    filtered = merged[
        (merged["experience"].fillna(0) >= min_exp)
        & (merged["authenticity"].fillna(0) >= min_auth)
        & (merged["behavior"].fillna(0) >= min_beh)
        & (merged["production"].fillna(0) >= min_prod)
    ]

    if location != "All":
        filtered = filtered[filtered["location"] == location]

    if query:
        q = query.lower()
        filtered = filtered[
            filtered["candidate_id"].astype(str).str.lower().str.contains(q)
            | filtered["role"].astype(str).str.lower().str.contains(q)
            | filtered["reasoning"].astype(str).str.lower().str.contains(q)
        ]

    table_cols = [c for c in ["candidate_id", "role", "experience", "score", "authenticity", "production", "behavior"] if c in filtered.columns]
    render_candidate_table(filtered[table_cols].sort_values(by="score", ascending=False), key="discovery-table")
