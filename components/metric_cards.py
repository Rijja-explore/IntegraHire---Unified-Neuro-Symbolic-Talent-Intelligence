"""Metric card components."""

from __future__ import annotations

import streamlit as st


def render_metric_row(metrics: list[tuple[str, str, str]]) -> None:
    cols = st.columns(len(metrics))
    for col, (label, value, delta) in zip(cols, metrics):
        with col:
            st.markdown('<div class="ih-card">', unsafe_allow_html=True)
            st.metric(label=label, value=value, delta=delta)
            st.markdown("</div>", unsafe_allow_html=True)
