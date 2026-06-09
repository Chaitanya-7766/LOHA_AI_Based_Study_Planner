import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import date, timedelta
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ml_engine import detect_performance_trend, calculate_streak
from pages_loha.ui_helpers import page_header, panel_open, panel_close, section_header, COLS
import db

def show():
    st.title("Analytics")
    st.caption("Productivity insights & performance analysis")
    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)

    logs     = st.session_state.get("progress_log", [])
    subjects = st.session_state.get("subjects", [])
    has_logs = len(logs) >= 1

    # ── Empty state ───────────────────────────────────────────────────
    if not has_logs:
        st.markdown("""
        <div class="panel">
            <div class="pb">
                <div class="empty">
                    <div class="empty-ico">📊</div>
                    <b style="color:var(--txt);">No data yet</b><br>
                    Log study sessions using the <b style="color:var(--acc);">Focus Timer</b>
                    and add test scores below to see your analytics.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        _add_score_panel(subjects)
        return

    df = pd.DataFrame(logs)
    df["score"]        = pd.to_numeric(df["score"], errors="coerce").fillna(0)
    df["duration_mins"]= pd.to_numeric(df.get("duration_mins", 25), errors="coerce").fillna(25) if "duration_mins" in df.columns else 25

    streak   = calculate_streak(df["date"].tolist())
    pred     = detect_performance_trend(df["score"].tolist())
    trend_c  = {"improving":"#10b981","declining":"#ef4444","stable":"#f59e0b"}.get(pred.get("trend","stable"),"#5a7090")
    done_n   = int(df["completed_topics"].sum()) if "completed_topics" in df.columns else 0
    avg_sc   = round(df["score"].mean(), 1)
    proj     = pred.get("projected_next","—")

    # ── Stat cards ────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="cgrid">
        <div class="scard sc"><div class="sico">📋</div><div class="slbl">Total Sessions</div><div class="sval">{len(df)}</div></div>
        <div class="scard sp"><div class="sico">📊</div><div class="slbl">Avg Score</div><div class="sval">{avg_sc}%</div></div>
        <div class="scard sa"><div class="sico">🔥</div><div class="slbl">Streak</div><div class="sval">{streak}d</div></div>
        <div class="scard sg"><div class="sico">📈</div><div class="slbl">Predicted Next</div><div class="sval">{proj}%</div></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Activity Heatmap ──────────────────────────────────────────────
    today_d = date.today()
    start_d = today_d - timedelta(days=55)
    daily   = df.groupby("date")["score"].count().to_dict()
    mx      = max(daily.values()) if daily else 1
    cur     = start_d - timedelta(days=start_d.weekday())
    day_lbls= ["M","T","W","T","F","S","S"]

    hm = "<div style='display:flex;gap:9px;overflow-x:auto;padding-bottom:5px;'>"
    while cur <= today_d:
        hm += f"<div style='display:flex;flex-direction:column;gap:1px;'>"
        hm += f"<div style='font-family:\"DM Mono\",monospace;font-size:9px;color:var(--muted);text-align:center;margin-bottom:3px;'>{day_lbls[cur.weekday()]}</div>"
        for di in range(7):
            cd  = cur + timedelta(days=di)
            if cd > today_d:
                hm += "<div class='hcell'></div>"
                continue
            k   = cd.strftime("%Y-%m-%d")
            cnt = daily.get(k, 0)
            v   = 0 if cnt == 0 else min(5, max(1, int(cnt/mx*5)))
            dv  = f'data-v="{v}"' if v > 0 else ""
            hm += f"<div class='hcell' {dv} title='{k}: {cnt} sessions'></div>"
        hm += "</div>"
        cur += timedelta(weeks=1)
    hm += "</div>"
    hm += """<div style='display:flex;align-items:center;gap:6px;margin-top:9px;'>
        <span style='font-size:10px;color:var(--muted);'>Less</span>
        <div style='width:12px;height:12px;border-radius:2px;background:var(--sur2);border:1px solid var(--brd);'></div>
        <div style='width:12px;height:12px;border-radius:2px;background:rgba(0,212,255,.15);'></div>
        <div style='width:12px;height:12px;border-radius:2px;background:rgba(0,212,255,.35);'></div>
        <div style='width:12px;height:12px;border-radius:2px;background:rgba(0,212,255,.6);'></div>
        <div style='width:12px;height:12px;border-radius:2px;background:var(--acc);'></div>
        <span style='font-size:10px;color:var(--muted);'>More</span>
    </div>"""

    st.markdown(panel_open("Study Activity Heatmap","8 WEEKS") + hm + panel_close(),
                unsafe_allow_html=True)

    # ── Charts row ────────────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        daily_avg = df.groupby("date")["score"].mean().reset_index()
        daily_avg.columns = ["Date","Score"]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily_avg["Date"], y=daily_avg["Score"],
            mode="lines+markers", name="Score",
            line=dict(color="#00d4ff",width=2), marker=dict(size=6),
            fill="tozeroy", fillcolor="rgba(0,212,255,.08)"))
        if len(daily_avg) >= 2:
            xn = list(range(len(daily_avg)))
            z  = np.polyfit(xn, daily_avg["Score"].values, 1)
            p  = np.poly1d(z)
            fig.add_trace(go.Scatter(x=daily_avg["Date"], y=[p(i) for i in xn],
                mode="lines", name="Trend",
                line=dict(color=trend_c, width=1.5, dash="dash")))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,20,32,1)",
            font_color="#5a7090", xaxis=dict(gridcolor="rgba(30,45,69,1)"),
            yaxis=dict(gridcolor="rgba(30,45,69,1)", range=[0,105]),
            legend=dict(orientation="h"), margin=dict(t=5,b=5), height=220)
        st.markdown(section_header("Score Trend","ALL SUBJECTS"), unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        if "subject" in df.columns and df["subject"].notna().any():
            subj_stats = df.groupby("subject").agg(
                avg_score=("score","mean"), sessions=("score","count")).reset_index()
            fig2 = px.bar(subj_stats, x="avg_score", y="subject", orientation="h",
                color="avg_score",
                color_continuous_scale=["#ef4444","#f59e0b","#10b981"],
                range_color=[40,100], text="sessions")
            fig2.update_traces(texttemplate="%{text} sessions", textposition="inside")
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,20,32,1)",
                font_color="#5a7090", showlegend=False,
                xaxis=dict(gridcolor="rgba(30,45,69,1)", range=[0,105]),
                yaxis=dict(gridcolor="rgba(30,45,69,1)"),
                margin=dict(t=5,b=5), height=220)
            st.markdown(section_header("Score by Subject"), unsafe_allow_html=True)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.markdown(panel_open("Score by Subject") +
                "<div class='empty'><div class='empty-ico'>📚</div>Log sessions with subject names to see breakdown.</div>" +
                panel_close(), unsafe_allow_html=True)

    # ── Add Test Score ─────────────────────────────────────────────────
    _add_score_panel(subjects)

    # ── ML Insights (only with real data) ────────────────────────────
    if len(df) >= 3:
        slope = pred.get("slope", 0)
        if "day_of_week" not in df.columns:
            df["day_of_week"] = pd.to_datetime(df["date"]).dt.day_name()
        day_counts     = df["day_of_week"].value_counts()
        best_day_label = day_counts.idxmax() if not day_counts.empty else "—"
        weak_subj      = df.groupby("subject")["score"].mean().idxmin() \
                         if "subject" in df.columns and df["subject"].notna().any() else "—"

        ins_html = f"""
        <div class='ic'>
            <div class='icico i{"g" if slope>0 else "w"}'>{"📈" if slope>0 else "📉" if slope<0 else "➡️"}</div>
            <div><div class='ictxt'><strong>Learning Trajectory</strong><br>
            {pred.get('trend','stable').capitalize()} · Slope: {slope:+.2f} pts/session.
            {'Keep going!' if slope>0 else 'Study more consistently.' if slope<0 else 'Push for improvement.'}</div></div>
        </div>
        <div class='ic'>
            <div class='icico ii'>📅</div>
            <div><div class='ictxt'><strong>Most Productive Day</strong><br>
            <span style='color:var(--acc);'>{best_day_label}</span> has the most sessions. Schedule hard topics then.</div></div>
        </div>
        <div class='ic'>
            <div class='icico iw'>⚠️</div>
            <div><div class='ictxt'><strong>Needs Attention</strong><br>
            <span style='color:var(--acc3);'>{weak_subj}</span> has your lowest average. Allocate more time here.</div></div>
        </div>"""
        st.markdown(panel_open("🤖 ML-Powered Insights","AI") + ins_html + panel_close(),
                    unsafe_allow_html=True)


def _add_score_panel(subjects):
    snames = [s["name"] for s in subjects]
    st.markdown(section_header("Add Test Score"), unsafe_allow_html=True)
    sc1, sc2, sc3, sc4 = st.columns([2,1,1,1])
    sc_subj = sc1.selectbox("Subject", snames, key="an_subj", label_visibility="collapsed") \
              if snames else sc1.text_input("Subject", placeholder="e.g. Machine Learning",
                                             key="an_subj_t", label_visibility="collapsed")
    sc_val  = sc2.number_input("Score %", 0, 100, 75, key="an_val", label_visibility="collapsed")
    sc_date = sc3.date_input("Date", date.today(), key="an_date", label_visibility="collapsed")
    if sc4.button("Add Score", key="an_add", use_container_width=True):
        entry = {"subject": sc_subj, "topic": "Test",
                 "date": sc_date.strftime("%Y-%m-%d"),
                 "score": sc_val, "difficulty": 3,
                 "completed": True, "completed_topics": 1, "duration_mins": 0}
        if "progress_log" not in st.session_state:
            st.session_state.progress_log = []
        st.session_state.progress_log.append(entry)
        try:
            db.save_progress(entry)
        except:
            pass
        st.success("✅ Score added!")
        st.rerun()
