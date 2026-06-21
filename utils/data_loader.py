"""Data loading utilities for IntegraHire UI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
import streamlit as st


@st.cache_data(show_spinner=False)
def load_submission_csv(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        return pd.DataFrame(columns=["candidate_id", "rank", "score", "reasoning"])
    return pd.read_csv(p)


@st.cache_data(show_spinner=False)
def load_json(path: str | Path) -> Any:
    p = Path(path)
    if not p.exists():
        return None
    with p.open("r", encoding="utf-8") as fh:
        return json.load(fh)


@st.cache_data(show_spinner=False)
def load_candidates_json(path: str | Path) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    data = load_json(p)
    if isinstance(data, list):
        return data
    return []


@st.cache_data(show_spinner=False)
def load_candidates_jsonl(path: str | Path) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []

    rows: List[Dict[str, Any]] = []
    with p.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def candidates_to_dataframe(candidates: List[Dict[str, Any]]) -> pd.DataFrame:
    records: List[Dict[str, Any]] = []
    for c in candidates:
        profile = c.get("profile", {})
        redrob = c.get("redrob_signals", c.get("behavioral_signals", {}))
        records.append(
            {
                "candidate_id": c.get("candidate_id", ""),
                "role": profile.get("current_title", "Unknown"),
                "location": profile.get("location", "Unknown"),
                "experience": profile.get("years_of_experience", 0),
                "authenticity": 100 - float(redrob.get("profile_completeness_score", 55)),
                "behavior": float(redrob.get("recruiter_response_rate", 0.5)) * 100,
                "production": float(redrob.get("github_activity_score", 50)),
            }
        )
    return pd.DataFrame(records)


def merge_rank_with_candidates(rank_df: pd.DataFrame, cand_df: pd.DataFrame) -> pd.DataFrame:
    if rank_df.empty and cand_df.empty:
        return pd.DataFrame()
    if rank_df.empty:
        return cand_df
    if cand_df.empty:
        return rank_df
    merged = rank_df.merge(cand_df, on="candidate_id", how="left")
    merged["final_score"] = merged.get("score", 0.0)
    return merged


def load_default_datasets() -> Tuple[pd.DataFrame, pd.DataFrame, List[Dict[str, Any]], List[Dict[str, Any]]]:
    ranked = load_submission_csv("test_submission.csv")
    top100 = load_json("test_submission.csv.top100.json") or []
    candidates = load_candidates_jsonl("test_candidates.jsonl")
    if not candidates:
        candidates = load_candidates_json("sample_candidates.json")
    cand_df = candidates_to_dataframe(candidates)
    merged = merge_rank_with_candidates(ranked, cand_df)
    return ranked, merged, candidates, top100
