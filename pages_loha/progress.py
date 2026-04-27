import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import date
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ml_engine import detect_performance_trend, calculate_streak
from pages_loha.ui_helpers import page_header, stat_card, section_header, COLS
import db

def show():
    st.markdown(page_header("Progress Tracker", "Log sessions & get ML-powered performance predictions"), unsafe_allow_html=True)
    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)
    if "progress_log" not in st.session_state: st.session_state.progress_log = []

    # Log session form
    st.markdown(section_header("Log a Study Session", "NEW"), unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    subject    = c1.text_input("Subject", placeholder="e.g. Machine Learning", key="pg_subj")
    topic      = c2.text_input("Topic Studied", placeholder="e.g. Neural Networks", key="pg_topic")
    study_date = c3.date_input("Date", date.today(), key="pg_date")
    c4,c5,c6 = st.columns(3)
    score      = c4.slider("Self-Assessment Score (%)", 0,100,70, key="pg_score")
    difficulty = c5.slider("Topic Difficulty (1–5)", 1,5,3, key="pg_diff")
    completed  = c6.checkbox("✅ Completed?", value=True, key="pg_done")
    if st.button("📝 Log Session", key="pg_log", use_container_width=True):
        entry = {"subject":subject,"topic":topic,"date":study_date.strftime("%Y-%m-%d"),"score":score,"difficulty":difficulty,"completed":completed,"completed_topics":1 if completed else 0}
        st.session_state.progress_log.append(entry)
        try: db.save_progress(entry); st.success("✅ Session logged & saved to Supabase!")
        except: st.success("✅ Session logged locally!")

    col_load, _ = st.columns([1,3])
    if col_load.button("🔄 Load from Supabase", key="pg_load"):
        try:
            remote = db.get_progress()
            if remote: st.session_state.progress_log = remote; st.success(f"Loaded {len(remote)} records!")
        except: st.warning("Supabase not configured.")

    logs = st.session_state.progress_log
    if not logs:
        st.markdown("<div class='panel'><div class='pb'><div class='empty'><div class='empty-ico'>📋</div>No sessions logged yet. Log your first session above!</div></div></div>", unsafe_allow_html=True)
        return

    df = pd.DataFrame(logs)
    df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0)
    streak      = calculate_streak(df["date"].tolist())
    prediction  = detect_performance_trend(df["score"].tolist())
    completed_n = int(df["completed_topics"].sum()) if "completed_topics" in df.columns else 0
    trend_color = {"improving":"#10b981","declining":"#ef4444","stable":"#f59e0b"}.get(prediction.get("trend","stable"),"#5a7090")

    # Stat cards
    cards = "".join([
        stat_card("📋","Sessions Logged",len(df),"sc"),
        stat_card("📊","Avg Score",f"{round(df['score'].mean(),1)}%","sp"),
        stat_card("🔥","Day Streak",f"{streak}d","sa"),
        stat_card("✅","Topics Completed",completed_n,"sg"),
    ])
    st.markdown(f"<div class='cgrid'>{cards}</div>", unsafe_allow_html=True)

    # ML Prediction panel
    pred_next = prediction.get('projected_next','—')
    trend_lbl = prediction.get('trend','stable').capitalize()
    avg_s     = prediction.get('avg_score','—')
    st.markdown(f"""
    <div class='panel'>
        <div class='ph'><span class='ptitle'>🤖 ML Performance Prediction</span><span class='ptag'>LINEAR REGRESSION</span></div>
        <div class='pb'>
            <div style='display:grid;grid-template-columns:repeat(3,1fr);gap:12px;'>
                <div style='background:var(--sur2);border:1px solid var(--brd);border-left:3px solid var(--acc2);border-radius:10px;padding:14px;text-align:center;'>
                    <div style='font-family:Syne;color:var(--acc2);font-size:1.6rem;font-weight:800;'>{pred_next}%</div>
                    <div style='font-size:10px;color:var(--muted);margin-top:4px;'>Projected Next Score</div>
                </div>
                <div style='background:var(--sur2);border:1px solid var(--brd);border-radius:10px;padding:14px;text-align:center;'>
                    <div style='font-size:1.4rem;color:{trend_color};'>{trend_lbl}</div>
                    <div style='font-size:10px;color:var(--muted);margin-top:4px;'>Learning Trend</div>
                    <div style='font-size:10px;color:var(--muted);'>{prediction.get('message','')[:60]}</div>
                </div>
                <div style='background:var(--sur2);border:1px solid var(--brd);border-left:3px solid var(--acc4);border-radius:10px;padding:14px;text-align:center;'>
                    <div style='font-family:Syne;color:var(--acc4);font-size:1.6rem;font-weight:800;'>{avg_s}%</div>
                    <div style='font-size:10px;color:var(--muted);margin-top:4px;'>Historical Average</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Charts row
    c1,c2 = st.columns(2)
    with c1:
        if len(df) >= 2:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["date"],y=df["score"],mode="lines+markers",name="Score",
                line=dict(color="#00d4ff",width=2),marker=dict(size=7,color="#00d4ff"),
                fill="tozeroy",fillcolor="rgba(0,212,255,0.08)"))
            if len(df)>=3:
                x_n = list(range(len(df)))
                z=np.polyfit(x_n,df["score"].values,1); p=np.poly1d(z)
                fig.add_trace(go.Scatter(x=df["date"],y=[p(i) for i in x_n],mode="lines",name="Trend",line=dict(color=trend_color,width=1.5,dash="dash")))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(13,20,32,1)",font_color="#5a7090",
                xaxis=dict(gridcolor="rgba(30,45,69,1)"),yaxis=dict(gridcolor="rgba(30,45,69,1)",range=[0,105]),
                legend=dict(orientation="h"),margin=dict(t=5,b=5),height=220)
            st.markdown(section_header("📈 Score Over Time"), unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        if "subject" in df.columns and df["subject"].notna().any():
            subj_avg = df.groupby("subject")["score"].mean().reset_index()
            subj_avg.columns = ["Subject","Avg Score"]
            fig2 = px.bar(subj_avg,x="Subject",y="Avg Score",color="Avg Score",
                color_continuous_scale=["#ef4444","#f59e0b","#10b981"],range_color=[0,100])
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(13,20,32,1)",font_color="#5a7090",showlegend=False,
                xaxis=dict(gridcolor="rgba(30,45,69,1)"),yaxis=dict(gridcolor="rgba(30,45,69,1)"),margin=dict(t=5,b=5),height=220)
            st.markdown(section_header("📊 Score by Subject"), unsafe_allow_html=True)
            st.plotly_chart(fig2, use_container_width=True)

    # Table
    st.markdown(section_header("📋 All Sessions"), unsafe_allow_html=True)
    display_cols = [c for c in ["date","subject","topic","score","difficulty","completed"] if c in df.columns]
    st.dataframe(df[display_cols],use_container_width=True,hide_index=True)

    if st.button("🗑️ Clear Sessions", key="pg_clear"):
        st.session_state.progress_log=[]; st.rerun()
