import sys
import pathlib
import streamlit as st
import json

# Ensure workspace root is on sys.path so demo can be run from demo/ or repo root
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from orchestrator.merger import merge_records
from orchestrator.pipeline import run_pipeline
from reasoning.generator import generate_reasoning_for
from export.csv_writer import write_submission_csv
from common.schemas import CandidateRecord
import os
import tempfile

# prefer workspace candidates.jsonl if present
WORKSPACE_CANDIDATES = os.path.join(str(pathlib.Path(__file__).resolve().parents[1]), "candidates.jsonl")
WORKSPACE_SAMPLE_SUBMISSION = os.path.join(str(pathlib.Path(__file__).resolve().parents[1]), "sample_submission.csv")



st.set_page_config(page_title="RCT Demo")

st.title("Recruiter Cognitive Twin — Demo")

default_jd = "Senior AI Engineer — Founding Team\n..."  # abbreviated; JD fixed internally
jd = st.text_area("Job Description (text)", value=default_jd, height=250)
ret_file = st.file_uploader("Upload retrieval JSON", type=["json"])
rank_file = st.file_uploader("Upload ranking JSON", type=["json"])
use_workspace_candidates = False
if os.path.exists(WORKSPACE_CANDIDATES):
    use_workspace_candidates = st.checkbox(f"Use workspace candidates.jsonl ({WORKSPACE_CANDIDATES})", value=True)
else:
    st.info("No local candidates.jsonl detected in workspace; please upload candidate profiles if needed.")


if st.button("Process"):
    if ret_file and rank_file:
        with tempfile.TemporaryDirectory() as td:
            ret_path = os.path.join(td, "retrieval.json")
            rank_path = os.path.join(td, "ranking.json")
            out_path = os.path.join(td, "submission.csv")
            # save uploaded files
            with open(ret_path, "wb") as f:
                f.write(ret_file.getbuffer())
            with open(rank_path, "wb") as f:
                f.write(rank_file.getbuffer())

            candidates_path = WORKSPACE_CANDIDATES if use_workspace_candidates and os.path.exists(WORKSPACE_CANDIDATES) else None
            jd_text_to_pass = jd.strip() if jd.strip() else None
            try:
                run_pipeline(ret_path, rank_path, out_path, candidates_jsonl=candidates_path, jd_text=jd_text_to_pass)
            except Exception as e:
                st.error(f"Pipeline failed: {e}")
            else:
                # read top 10 from generated debug JSON
                debug_path = out_path + ".top100.json"
                if os.path.exists(debug_path):
                    with open(debug_path, "r", encoding="utf-8") as df:
                        debug = json.load(df)
                    top10 = debug[:10]
                    st.subheader("Top 10 Candidates")
                    rows = []
                    for idx, r in enumerate(top10, start=1):
                        rows.append({
                            "rank": idx,
                            "candidate_id": r.get("candidate_id"),
                            "score": r.get("final_score"),
                            "reasoning": r.get("reasoning"),
                        })
                    st.table(rows)

                # provide download
                if os.path.exists(out_path):
                    with open(out_path, "rb") as f:
                        data = f.read()
                    st.download_button("Download submission CSV", data, file_name="submission.csv", mime="text/csv")
                else:
                    st.warning("Submission CSV not found.")
    elif use_workspace_candidates and os.path.exists(WORKSPACE_SAMPLE_SUBMISSION):
        st.info("No retrieval/ranking files uploaded. Showing the local sample submission as a workspace preview.")
        with open(WORKSPACE_SAMPLE_SUBMISSION, "r", encoding="utf-8") as f:
            sample_csv = f.read()
        st.subheader("Submission CSV Preview")
        st.code(sample_csv, language="csv")
        with open(WORKSPACE_SAMPLE_SUBMISSION, "rb") as f:
            data = f.read()
        st.download_button("Download submission CSV", data, file_name="submission.csv", mime="text/csv")
    else:
        st.error("Upload retrieval and ranking JSON files, or enable workspace mode with a local sample submission available.")
