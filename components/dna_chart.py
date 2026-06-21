"""DNA radar chart component."""

from __future__ import annotations

import streamlit as st

from utils.charts import radar_chart


def render_dna_chart(dna_values: dict[str, float], title: str = "Candidate DNA") -> None:
    labels = list(dna_values.keys())
    values = [float(dna_values[k]) for k in labels]
    fig = radar_chart(labels, values, title)
    st.plotly_chart(fig, use_container_width=True)
