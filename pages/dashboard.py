"""Dashboard page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.candidate_table import render_candidate_table
from components.metric_cards import render_metric_row
from utils.charts import histogram


def render(data: dict) -> None:
    merged: pd.DataFrame = data["merged"]
    ranked: pd.DataFrame = data["ranked"]

    st.markdown('<div class="ih-title">Executive Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="ih-subtitle">Unified talent intelligence across retrieval, authenticity, behavior, and production fit.</div>', unsafe_allow_html=True)

    if merged.empty:
        st.warning("No ranking data available yet. Run rank.py to generate submission artifacts.")
        return

    metrics = [
        ("Total Candidates", f"{len(data['candidates'])}", "Candidate corpus"),
        ("Retrieved Candidates", f"{len(merged)}", "Scored list"),
        ("Top Ranked Candidates", f"{len(ranked)}", "Submission size"),
        ("Average Authenticity", f"{merged['authenticity'].fillna(0).mean():.1f}", "proxy"),
        ("Average Production Score", f"{merged['production'].fillna(0).mean():.1f}", "proxy"),
        ("Average Recruitability", f"{merged['behavior'].fillna(0).mean():.1f}", "proxy"),
    ]
    render_metric_row(metrics)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(histogram(merged, "score", "Candidate Score Distribution", "#2563EB"), use_container_width=True)
        st.plotly_chart(histogram(merged, "authenticity", "Authenticity Distribution", "#10B981"), use_container_width=True)
    with c2:
        st.plotly_chart(histogram(merged, "behavior", "Behavior Distribution", "#F59E0B"), use_container_width=True)
        st.plotly_chart(histogram(merged, "production", "Production Readiness Distribution", "#EF4444"), use_container_width=True)

    st.subheader("Top Candidates Preview")
    preview_cols = [c for c in ["rank", "candidate_id", "score", "authenticity", "production", "behavior", "reasoning"] if c in ranked.columns]
    render_candidate_table(ranked[preview_cols].head(20), key="top-preview")
