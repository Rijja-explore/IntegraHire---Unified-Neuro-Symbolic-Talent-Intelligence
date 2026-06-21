"""Score breakdown cards."""

from __future__ import annotations

import streamlit as st


def render_score_cards(scores: dict[str, float]) -> None:
    cols = st.columns(len(scores))
    for col, (name, val) in zip(cols, scores.items()):
        with col:
            st.markdown('<div class="ih-card">', unsafe_allow_html=True)
            st.metric(name, f"{float(val):.2f}")
            st.markdown("</div>", unsafe_allow_html=True)
