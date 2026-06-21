"""Theme helpers for IntegraHire Streamlit UI."""

from __future__ import annotations

import streamlit as st


PALETTE = {
    "primary": "#2563EB",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "background": "#0F172A",
    "cards": "#1E293B",
    "text": "#F8FAFC",
    "muted": "#94A3B8",
}


def inject_theme() -> None:
    """Inject custom CSS theme and reusable utility classes."""
    st.markdown(
        f"""
        <style>
            :root {{
                --ih-primary: {PALETTE['primary']};
                --ih-success: {PALETTE['success']};
                --ih-warning: {PALETTE['warning']};
                --ih-danger: {PALETTE['danger']};
                --ih-bg: {PALETTE['background']};
                --ih-card: {PALETTE['cards']};
                --ih-text: {PALETTE['text']};
                --ih-muted: {PALETTE['muted']};
            }}

            .stApp {{
                background:
                    radial-gradient(circle at 5% 10%, rgba(37,99,235,0.18), transparent 28%),
                    radial-gradient(circle at 90% 15%, rgba(16,185,129,0.12), transparent 22%),
                    linear-gradient(160deg, #0b1222 0%, var(--ih-bg) 55%, #111827 100%);
                color: var(--ih-text);
            }}

            [data-testid="stSidebar"] {{
                background: linear-gradient(180deg, #111827 0%, #0b1222 100%);
                border-right: 1px solid rgba(148,163,184,0.18);
            }}

            .ih-title {{
                font-size: 1.6rem;
                font-weight: 700;
                letter-spacing: 0.02em;
                color: var(--ih-text);
                margin-bottom: 0.4rem;
            }}

            .ih-subtitle {{
                color: var(--ih-muted);
                font-size: 0.95rem;
                margin-bottom: 1.2rem;
            }}

            .ih-card {{
                background: linear-gradient(180deg, rgba(30,41,59,0.95), rgba(15,23,42,0.96));
                border: 1px solid rgba(148,163,184,0.16);
                border-radius: 14px;
                padding: 14px 16px;
                box-shadow: 0 8px 30px rgba(2,6,23,0.22);
            }}

            .ih-pill {{
                display: inline-block;
                margin: 0.1rem 0.25rem 0.25rem 0;
                padding: 0.22rem 0.55rem;
                background: rgba(37,99,235,0.18);
                border: 1px solid rgba(37,99,235,0.35);
                border-radius: 999px;
                color: var(--ih-text);
                font-size: 0.78rem;
                font-weight: 600;
            }}

            .ih-footer {{
                margin-top: 2rem;
                color: var(--ih-muted);
                text-align: center;
                font-size: 0.82rem;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )
