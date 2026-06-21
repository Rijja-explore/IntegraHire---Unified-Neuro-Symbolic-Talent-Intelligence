"""Analytics and system intelligence page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.charts import box, histogram


def render(data: dict) -> None:
    merged: pd.DataFrame = data["merged"]
    st.markdown('<div class="ih-title">Analytics</div>', unsafe_allow_html=True)

    if merged.empty:
        st.warning("No analytics data found.")
        return

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(histogram(merged, "production", "Production Readiness Distribution", "#10B981"), use_container_width=True)
        st.plotly_chart(histogram(merged, "behavior", "Behavioral Metrics", "#F59E0B"), use_container_width=True)
        st.plotly_chart(box(merged, "score", "Ranking Score Distribution", "#2563EB"), use_container_width=True)

    with c2:
        st.plotly_chart(histogram(merged, "experience", "Skill/Experience Distribution", "#2563EB"), use_container_width=True)
        st.plotly_chart(histogram(merged, "authenticity", "Authenticity Heatmap Proxy", "#EF4444"), use_container_width=True)
        st.plotly_chart(histogram(merged, "score", "Candidate Quality Distribution", "#10B981"), use_container_width=True)

    st.subheader("System Intelligence")
    st.markdown(
        """
```mermaid
graph TD
  A[Job Description] --> B[Hybrid Retrieval]
  B --> C[Authenticity Engine]
  C --> D[Trajectory Engine]
  D --> E[Production Engine]
  E --> F[Behavior Engine]
  F --> G[Candidate DNA]
  G --> H[Ranking Engine]
  H --> I[Reasoning Generator]
```
        """
    )
