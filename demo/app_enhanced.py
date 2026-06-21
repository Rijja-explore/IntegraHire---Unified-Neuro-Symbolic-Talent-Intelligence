"""Enhanced RCT Streamlit Demo with Leaderboard, Evaluation, and Mock Data."""

import sys
import pathlib
import streamlit as st
import json
import tempfile
import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Ensure workspace root is on sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from orchestrator.pipeline import run_pipeline
from tools.mock_data_generator import save_mock_data
from evaluation.ndcg import ndcg_at_k

# ============= PAGE CONFIG & STYLING =============
st.set_page_config(
    page_title="RCT — Recruiter Cognitive Twin",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "🏆 Hackathon-Ready Ranking Engine"}
)

st.markdown("""
<style>
    .metric-box { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
        padding: 20px; border-radius: 10px; color: white; text-align: center; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .metric-value { font-size: 36px; font-weight: bold; margin: 10px 0; }
    .metric-label { font-size: 13px; opacity: 0.9; }
    .success-box { background: #d4edda; color: #155724; padding: 15px; border-radius: 8px; border-left: 4px solid #28a745; }
    .info-box { background: #d1ecf1; color: #0c5460; padding: 15px; border-radius: 8px; border-left: 4px solid #17a2b8; }
    .leaderboard-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 8px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ============= SIDEBAR CONFIG =============
with st.sidebar:
    st.markdown("# ⚙️ Configuration")
    st.divider()
    
    mode = st.radio(
        "Select Mode",
        ["🎯 Interactive Demo", "📊 Leaderboard", "🧪 Mock Data Test", "📈 Evaluation Metrics"],
        help="Choose operation mode"
    )
    
    st.divider()
    st.markdown("### Mock Data Settings")
    num_candidates = st.slider("Candidate Pool Size", 100, 2000, 500, 100)
    seed_val = st.slider("Random Seed", 1, 100, 42)
    
    st.divider()
    st.markdown("### System Info")
    st.caption(f"📦 Python 3.11+")
    st.caption(f"🔷 Streamlit 1.28+")
    st.caption(f"📊 Deterministic Ranking")
    st.caption(f"🚀 CPU-Only (5min)")

# ============= MAIN TITLE =============

st.title("🏆 Recruiter Cognitive Twin")
st.markdown("*Production-grade ranking engine with evaluation & leaderboard*")

# ============= MODE 1: INTERACTIVE DEMO =============
if mode == "🎯 Interactive Demo":
    st.header("Interactive Ranking Demo")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📝 Job Description")
        jd = st.text_area(
            "Enter Job Description",
            value="Senior AI Engineer — Founding Team\nRequired Skills: Python, Kubernetes, System Design\nExperience: 5+ years in ML/AI",
            height=200,
            label_visibility="collapsed"
        )
    
    with col2:
        st.subheader("📤 Input Configuration")
        input_mode = st.radio("Data Source", ["🔄 Generate Mock Data", "📁 Upload Files"], label_visibility="collapsed")
    
    st.divider()
    
    # Generate Mock Data Path
    if input_mode == "🔄 Generate Mock Data":
        st.info("✨ Will generate realistic mock data with semantic scores and behavior signals")
        
        if st.button("🚀 Generate & Process", use_container_width=True, type="primary"):
            progress_bar = st.progress(0)
            
            # Step 1: Generate data
            progress_bar.progress(15)
            st.status("Generating mock data...", state="running")
            retrieval, ranking, candidates = save_mock_data(num_candidates, seed_val)
            st.status("Mock data generated ✓", state="complete")
            progress_bar.progress(35)
            
            # Step 2: Save to temp files
            progress_bar.progress(45)
            st.status("Processing ranking pipeline...", state="running")
            
            with tempfile.TemporaryDirectory() as td:
                ret_path = os.path.join(td, "retrieval.json")
                rank_path = os.path.join(td, "ranking.json")
                cand_path = os.path.join(td, "candidates.jsonl")
                out_path = os.path.join(td, "submission.csv")
                
                # Write files
                with open(ret_path, "w") as f:
                    json.dump(retrieval, f)
                with open(rank_path, "w") as f:
                    json.dump(ranking, f)
                with open(cand_path, "w") as f:
                    for c in candidates:
                        f.write(json.dumps(c) + "\n")
                
                progress_bar.progress(60)
                
                try:
                    # Run pipeline
                    run_pipeline(ret_path, rank_path, out_path, cand_path, jd.strip())
                    progress_bar.progress(85)
                    
                    # Read results
                    with open(out_path) as f:
                        df = pd.read_csv(f)
                    
                    progress_bar.progress(100)
                    st.status("Pipeline complete ✓", state="complete")
                    
                    # Display success metrics
                    st.markdown('<div class="success-box">✅ Ranking Complete!</div>', unsafe_allow_html=True)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Candidates", len(df), delta="Top 100 selected")
                    with col2:
                        st.metric("Max Score", f"{df['score'].iloc[0]:.4f}", delta="Highest ranked")
                    with col3:
                        st.metric("Avg Score", f"{df['score'].mean():.4f}", delta="Mean rank score")
                    with col4:
                        st.metric("Score Range", f"{df['score'].min():.4f}", delta="Lowest in top 100")
                    
                    st.divider()
                    
                    # Top 10 Table
                    st.subheader("🏅 Top 10 Candidates")
                    top10_df = df.head(10)[['candidate_id', 'rank', 'score', 'reasoning']].copy()
                    top10_df['score'] = top10_df['score'].apply(lambda x: f"{x:.6f}")
                    st.dataframe(top10_df, use_container_width=True, hide_index=True)
                    
                    # Visualizations
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig = px.histogram(df, x="score", nbins=25, title="Score Distribution", 
                                         labels={"score": "Final Score", "count": "Frequency"})
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=list(range(1, len(df)+1)), y=df['score'].values,
                                               mode='lines+markers', name='Score Trend',
                                               line=dict(color='#667eea', width=2)))
                        fig.update_layout(title="Score Monotonicity Check", height=400,
                                        xaxis_title="Rank", yaxis_title="Score")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Download
                    csv_data = df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Submission CSV",
                        csv_data,
                        "submission.csv",
                        "text/csv",
                        use_container_width=True,
                        type="secondary"
                    )
                    
                except Exception as e:
                    st.error(f"❌ Pipeline failed: {str(e)}")
    
    # Upload Files Path
    else:
        col1, col2 = st.columns(2)
        with col1:
            ret_file = st.file_uploader("Upload Retrieval JSON", type=["json"])
        with col2:
            rank_file = st.file_uploader("Upload Ranking JSON", type=["json"])
        
        use_workspace = st.checkbox("Use workspace candidates.jsonl", value=True)
        
        if st.button("🚀 Process", use_container_width=True, type="primary"):
            if ret_file and rank_file:
                with tempfile.TemporaryDirectory() as td:
                    ret_path = os.path.join(td, "retrieval.json")
                    rank_path = os.path.join(td, "ranking.json")
                    out_path = os.path.join(td, "submission.csv")
                    cand_path = None
                    
                    with open(ret_path, "wb") as f:
                        f.write(ret_file.getbuffer())
                    with open(rank_path, "wb") as f:
                        f.write(rank_file.getbuffer())
                    
                    if use_workspace and os.path.exists("../candidates.jsonl"):
                        cand_path = "../candidates.jsonl"
                    
                    try:
                        run_pipeline(ret_path, rank_path, out_path, cand_path, jd.strip())
                        with open(out_path) as f:
                            df = pd.read_csv(f)
                        
                        st.success(f"✅ Generated {len(df)} ranked candidates")
                        st.dataframe(df.head(10), use_container_width=True)
                        
                        st.download_button(
                            "📥 Download CSV",
                            df.to_csv(index=False),
                            "submission.csv",
                            "text/csv",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            else:
                st.error("Please upload both retrieval and ranking JSON files")

# ============= MODE 2: LEADERBOARD =============
elif mode == "📊 Leaderboard":
    st.header("🏆 Local Leaderboard Simulator")
    st.markdown("Simulate multiple ranking runs and compare performance")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        num_runs = st.slider("Number of Runs", 2, 10, 5)
    with col2:
        if st.button("🎲 Simulate", type="primary"):
            st.session_state.simulate = True
    
    if st.button("🎲 Run Leaderboard Simulation", use_container_width=True, type="primary"):
        leaderboard_data = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for run_id in range(1, num_runs + 1):
            seed = 40 + run_id
            status_text.text(f"Running simulation {run_id}/{num_runs}...")
            progress_bar.progress(run_id / num_runs)
            
            try:
                retrieval, ranking, candidates = save_mock_data(num_candidates, seed)
                
                with tempfile.TemporaryDirectory() as td:
                    ret_path = os.path.join(td, "retrieval.json")
                    rank_path = os.path.join(td, "ranking.json")
                    cand_path = os.path.join(td, "candidates.jsonl")
                    out_path = os.path.join(td, "submission.csv")
                    
                    with open(ret_path, "w") as f:
                        json.dump(retrieval, f)
                    with open(rank_path, "w") as f:
                        json.dump(ranking, f)
                    with open(cand_path, "w") as f:
                        for c in candidates:
                            f.write(json.dumps(c) + "\n")
                    
                    run_pipeline(ret_path, rank_path, out_path, cand_path)
                    
                    with open(out_path) as f:
                        df = pd.read_csv(f)
                    
                    # Calculate metrics
                    top_score = df['score'].iloc[0]
                    avg_score = df['score'].mean()
                    score_std = df['score'].std()
                    
                    # Simulate NDCG
                    gold = {f"C{i}": max(0, 1 - i/100) for i in range(100)}
                    pred = df['candidate_id'].tolist()
                    ndcg = ndcg_at_k(gold, pred, 100)
                    
                    leaderboard_data.append({
                        "🏅 Rank": run_id,
                        "Run ID": f"Run #{run_id}",
                        "Seed": seed,
                        "Candidates": len(df),
                        "📈 Top Score": round(top_score, 4),
                        "Avg Score": round(avg_score, 4),
                        "Std Dev": round(score_std, 4),
                        "NDCG@100": round(ndcg, 4),
                        "Timestamp": datetime.now().strftime("%H:%M:%S")
                    })
            except Exception as e:
                st.warning(f"Run {run_id} failed: {str(e)}")
        
        progress_bar.progress(1.0)
        status_text.empty()
        
        # Display leaderboard
        lb_df = pd.DataFrame(leaderboard_data)
        st.subheader("📊 Leaderboard Results")
        if lb_df.empty:
            st.info("Run simulation to populate leaderboard.")
        else:
            top_score_col = (
                "📈 Top Score"
                if "📈 Top Score" in lb_df.columns
                else ("Top Score" if "Top Score" in lb_df.columns else lb_df.columns[0])
            )
            st.dataframe(
                lb_df.sort_values(top_score_col, ascending=False),
                use_container_width=True,
                hide_index=True,
            )


        # Charts
        col1, col2 = st.columns(2)

        # Resolve leaderboard column names safely (emoji columns may differ)
        run_id_col = "Run ID" if "Run ID" in lb_df.columns else ("Run" if "Run" in lb_df.columns else None)
        top_score_col = (
            "📈 Top Score" if "📈 Top Score" in lb_df.columns else ("Top Score" if "Top Score" in lb_df.columns else None)
        )
        avg_score_col = "Avg Score" if "Avg Score" in lb_df.columns else None
        ndcg_col = "NDCG@100" if "NDCG@100" in lb_df.columns else None

        with col1:
            fig = go.Figure()
            if run_id_col and top_score_col and avg_score_col:
                fig.add_trace(go.Bar(x=lb_df[run_id_col], y=lb_df[top_score_col], name="Top Score", marker_color="#667eea"))
                fig.add_trace(go.Bar(x=lb_df[run_id_col], y=lb_df[avg_score_col], name="Avg Score", marker_color="#764ba2"))
                fig.update_layout(title="Score Comparison", barmode='group', height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Leaderboard columns unavailable for chart rendering.")

        with col2:
            if run_id_col and ndcg_col:
                fig = px.line(lb_df, x=run_id_col, y=ndcg_col, markers=True, title="NDCG Trend", line_shape="linear")
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Leaderboard columns unavailable for NDCG chart rendering.")


# ============= MODE 3: MOCK DATA TEST =============
elif mode == "🧪 Mock Data Test":
    st.header("Mock Data Generation & Inspection")
    
    if st.button("🔄 Generate Test Data", use_container_width=True, type="primary"):
        st.subheader("Generating Mock Data...")
        
        retrieval, ranking, candidates = save_mock_data(num_candidates, seed_val)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("📊 Retrieval Data")
            st.metric("Records", len(retrieval))
            st.json(retrieval[0])
        
        with col2:
            st.subheader("⚡ Ranking Data")
            st.metric("Records", len(ranking))
            st.json(ranking[0])
        
        with col3:
            st.subheader("👤 Candidate Profile")
            st.metric("Records", len(candidates))
            st.json(candidates[0])
        
        st.divider()
        
        # Statistics
        st.subheader("📈 Data Statistics")
        col1, col2, col3 = st.columns(3)
        
        sem_scores = [r["semantic_score"] for r in retrieval]
        final_scores = [r["final_score"] for r in ranking]
        
        with col1:
            st.metric("Avg Semantic Score", f"{sum(sem_scores)/len(sem_scores):.4f}")
            st.metric("Max Semantic Score", f"{max(sem_scores):.4f}")
            st.metric("Min Semantic Score", f"{min(sem_scores):.4f}")
        
        with col2:
            st.metric("Avg Final Score", f"{sum(final_scores)/len(final_scores):.4f}")
            st.metric("Max Final Score", f"{max(final_scores):.4f}")
            st.metric("Min Final Score", f"{min(final_scores):.4f}")
        
        with col3:
            skills_count = sum(len(c["skills"]) for c in candidates)
            st.metric("Total Skills", skills_count)
            st.metric("Avg Skills/Candidate", f"{skills_count/len(candidates):.1f}")
            st.metric("Total Companies", len(set(c["profile"]["current_company"] for c in candidates)))

# ============= MODE 4: EVALUATION METRICS =============
elif mode == "📈 Evaluation Metrics":
    st.header("Evaluation Metrics Dashboard")
    st.markdown("Performance metrics for ranking quality assessment")
    
    if st.button("📊 Calculate Metrics", use_container_width=True, type="primary"):
        retrieval, ranking, candidates = save_mock_data(num_candidates, seed_val)
        
        with tempfile.TemporaryDirectory() as td:
            ret_path = os.path.join(td, "retrieval.json")
            rank_path = os.path.join(td, "ranking.json")
            cand_path = os.path.join(td, "candidates.jsonl")
            out_path = os.path.join(td, "submission.csv")
            
            with open(ret_path, "w") as f:
                json.dump(retrieval, f)
            with open(rank_path, "w") as f:
                json.dump(ranking, f)
            with open(cand_path, "w") as f:
                for c in candidates:
                    f.write(json.dumps(c) + "\n")
            
            try:
                run_pipeline(ret_path, rank_path, out_path, cand_path)
                
                with open(out_path) as f:
                    df = pd.read_csv(f)
                
                # Simulate gold standard
                gold = {f"CAND_{i:07d}": max(0, 1 - i/500) for i in range(500)}
                pred = df['candidate_id'].tolist()
                
                # Calculate metrics
                ndcg_10 = ndcg_at_k(gold, pred, 10)
                ndcg_100 = ndcg_at_k(gold, pred, 100)
                precision_10 = len([p for p in pred[:10] if p in gold and gold[p] > 0.5]) / 10
                recall = len([p for p in pred if p in gold and gold[p] > 0.3]) / min(100, sum(1 for v in gold.values() if v > 0.3))
                
                st.markdown("### 📊 Core Metrics")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("NDCG@10", f"{ndcg_10:.4f}", delta="Ranking quality (top 10)")
                with col2:
                    st.metric("NDCG@100", f"{ndcg_100:.4f}", delta="Ranking quality (full)")
                with col3:
                    st.metric("Precision@10", f"{precision_10:.4f}", delta="Relevant in top 10")
                with col4:
                    st.metric("Recall@100", f"{recall:.4f}", delta="Coverage in top 100")
                
                st.divider()
                
                # Detailed breakdown
                st.markdown("### 📈 Detailed Analysis")
                col1, col2 = st.columns(2)
                
                with col1:
                    # NDCG curve
                    k_values = [5, 10, 20, 50, 100]
                    ndcg_values = [ndcg_at_k(gold, pred, k) for k in k_values]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=k_values, y=ndcg_values, mode='lines+markers',
                                           line=dict(color='#667eea', width=3), marker=dict(size=10)))
                    fig.update_layout(title="NDCG@K Curve", xaxis_title="K", yaxis_title="NDCG Score", height=400)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Score distribution
                    fig = px.histogram(df, x="score", nbins=30, title="Score Distribution",
                                     labels={"score": "Final Score"})
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                
                st.success("✅ Evaluation complete!")
                
            except Exception as e:
                st.error(f"❌ Evaluation failed: {str(e)}")

# ============= FOOTER =============
st.divider()
st.markdown("""
<center>
<p style='font-size: 12px; color: #666;'>
Built with ❤️ for hackathons | Python 3.11+ | Streamlit 1.28+ | Deterministic Ranking Engine
</p>
</center>
""", unsafe_allow_html=True)
