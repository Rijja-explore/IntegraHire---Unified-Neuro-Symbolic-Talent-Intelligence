"""Plotly chart helpers for IntegraHire UI."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


PLOT_THEME = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": "#F8FAFC"},
}


def histogram(df: pd.DataFrame, col: str, title: str, color: str) -> go.Figure:
    fig = px.histogram(df, x=col, nbins=20, opacity=0.9, color_discrete_sequence=[color], title=title)
    fig.update_layout(**PLOT_THEME, margin=dict(l=10, r=10, t=40, b=10))
    return fig


def box(df: pd.DataFrame, y: str, title: str, color: str) -> go.Figure:
    fig = px.box(df, y=y, points="all", color_discrete_sequence=[color], title=title)
    fig.update_layout(**PLOT_THEME, margin=dict(l=10, r=10, t=40, b=10))
    return fig


def radar_chart(labels: list[str], values: list[float], title: str, color: str = "#2563EB") -> go.Figure:
    theta = labels + [labels[0]]
    r = values + [values[0]]
    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=r,
            theta=theta,
            fill="toself",
            line=dict(color=color, width=2),
            fillcolor="rgba(37,99,235,0.28)",
            name="DNA",
        )
    )
    fig.update_layout(
        title=title,
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(148,163,184,0.2)")),
        **PLOT_THEME,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig


def timeline(companies: list[str], durations: list[int], title: str = "Career Timeline") -> go.Figure:
    df = pd.DataFrame({"Company": companies, "DurationMonths": durations})
    fig = px.bar(df, x="DurationMonths", y="Company", orientation="h", title=title, color="DurationMonths")
    fig.update_layout(**PLOT_THEME, margin=dict(l=10, r=10, t=40, b=10), coloraxis_showscale=False)
    return fig
