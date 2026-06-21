"""Candidate table component."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def render_candidate_table(df: pd.DataFrame, key: str = "table") -> None:
    if df.empty:
        st.info("No candidates to display.")
        return
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        key=key,
    )
