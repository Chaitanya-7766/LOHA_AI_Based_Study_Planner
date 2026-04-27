import streamlit as st
from datetime import date
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ml_engine import calculate_streak, compute_readiness_score
from pages_loha.ui_helpers import panel_open, panel_close, insight_card, subject_perf_bars, COLS

def show():
    subjects = st.session_state.get("subjects", [])
    logs     = st.session_state.get("progress_log", [])
    profile  = st.session_state.get("profile", {})

    # ── CLEAN HEADER (NO HTML BUG) ───────────────────────────────
    st.title("Dashboard")
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ── LOGIC ───────────────────────────────────────────────────
    exam_days = None
    if profile.get("exam_date"):
        try:
            ed = date.fromisoformat(str(profile["exam_date"])[:10])
            exam_days = max(0, (ed - date.today()).days)
        except:
            pass

    hrs    = round(sum(l.get("duration_mins", 25) for l in logs) / 60, 1) if logs else 0.0
    streak = calculate_streak([l.get("date","") for l in logs]) if logs else 0

    has_subjects = len(subjects) > 0
    has_logs     = len(logs) > 0

    avg_score = round(sum(s.get("avg_score",0) for s in subjects)/len(subjects), 1) if has_subjects else 0
    readiness = compute_readiness_score(subjects, min(len(logs),7), 0.7, exam_days or 30) if has_subjects and has_logs else 0

    # ── STAT CARDS ───────────────────────────────────────────────
    cols = st.columns(4)

    cols[0].markdown(f"""
    <div class="scard sc">
        <div class="sico">⏰</div><div class="slbl">Hours Studied</div>
        <div class="sval">{hrs if has_logs else "–"}</div>
        <div class="schg">{'This session' if has_logs else 'Log sessions to track'}</div>
    </div>""", unsafe_allow_html=True)

    cols[1].markdown(f"""
    <div class="scard sp">
        <div class="sico">✅</div><div class="slbl">Sessions Logged</div>
        <div class="sval">{len(logs) if has_logs else "–"}</div>
        <div class="schg">{'Total sessions' if has_logs else 'Use Focus Timer to log'}</div>
    </div>""", unsafe_allow_html=True)

    cols[2].markdown(f"""
    <div class="scard sa">
        <div class="sico">🎯</div><div class="slbl">Readiness Score</div>
        <div class="sval">{f'{readiness:.0f}%' if (has_subjects and has_logs) else '–'}</div>
        <div class="schg">{'On track 🎯' if readiness>=70 else ('Add subjects & log sessions' if not has_subjects else 'Log sessions to calculate')}</div>
    </div>""", unsafe_allow_html=True)

    cols[3].markdown(f"""
    <div class="scard sg">
        <div class="sico">🔥</div><div class="slbl">Study Streak</div>
        <div class="sval">{f'{streak}d' if has_logs else '–'}</div>
        <div class="schg">{'Keep it up!' if streak>1 else ('Start studying daily!' if has_logs else 'Study daily to build streak')}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── SUBJECT PERFORMANCE + AI INSIGHTS ─────────────────────────
    c1, c2 = st.columns(2)

    with c1:
        if has_subjects:
            content = subject_perf_bars(subjects)
        else:
            content = '<div class="empty"><div class="empty-ico">📚</div>No subjects yet.<br>Go to <b>Setup</b> to add your subjects.</div>'
        st.markdown(panel_open("Subject Performance","LIVE") + content + panel_close(), unsafe_allow_html=True)

    with c2:
        ins_html = ""

        if has_subjects:
            for s in subjects:
                sc, tgt = s.get("avg_score",0), s.get("target_score",80)
                if sc < tgt - 15:
                    ins_html += insight_card(
                        "⚠️",
                        f"Weak Area: {s['name']}",
                        f"Avg {round(sc)}% vs target {tgt}%. Focus {round((tgt-sc)/2)}h extra this week.",
                        "",
                        "w"
                    )

            if has_logs:
                ins_html += insight_card(
                    "📊",
                    "Readiness Updated",
                    f"Score {readiness:.0f}/100. {'On track! 🎯' if readiness>=75 else 'Focus on weak subjects.'}",
                    "",
                    "g"
                )

            if exam_days is not None:
                ins_html += insight_card(
                    "⏰",
                    f"{exam_days} Days Until Exam",
                    "Stay consistent with your daily schedule!",
                    "",
                    "i"
                )

            if not ins_html:
                ins_html = insight_card(
                    "📅",
                    "Schedule Ready",
                    "Generate your AI study schedule from the Schedule page.",
                    "",
                    "i"
                )

        # ── FINAL SAFE RENDER ─────────────────────────────────────
        if ins_html.strip():
            st.markdown(panel_open("AI Insights","LIVE") + ins_html + panel_close(), unsafe_allow_html=True)
        else:
            st.markdown(panel_open("AI Insights","LIVE") + '<div style="height:40px;"></div>' + panel_close(), unsafe_allow_html=True)

    # ── RECENT SESSIONS + WEEKLY CHART ───────────────────────────
    c3, c4 = st.columns(2)

    with c3:
        if has_logs:
            task_html = ""
            for l in logs[-5:][::-1]:
                c = COLS[hash(str(l.get("subject",""))) % len(COLS)]
                dur = l.get("duration_mins", 25)
                task_html += f"""
                <div style="display:flex;align-items:center;gap:9px;padding:9px 0;border-bottom:1px solid var(--brd);">
                    <div style="width:17px;height:17px;border-radius:50%;background:var(--acc4);
                                display:flex;align-items:center;justify-content:center;font-size:10px;color:#fff;">✓</div>
                    <span style="font-size:12px;flex:1;color:var(--txt);">{l.get('subject','')} · {l.get('topic','')}</span>
                    <span style="font-size:9px;padding:2px 7px;border-radius:20px;background:{c}18;color:{c};">{dur}min · {l.get('score',0)}%</span>
                </div>"""
        else:
            task_html = '<div class="empty"><div class="empty-ico">⏱️</div>No sessions yet.<br>Use the Focus Timer to log study sessions.</div>'

        st.markdown(panel_open("Recent Sessions") + task_html + panel_close(), unsafe_allow_html=True)

    with c4:
        day_lbl = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        totals  = [0.0]*7

        if has_logs:
            for l in logs:
                try:
                    d = date.fromisoformat(str(l.get("date","")))
                    totals[d.weekday()] += round(l.get("duration_mins",25)/60, 1)
                except:
                    pass

        mx = max(totals) or 1
        bars = ""

        for i,(d,h) in enumerate(zip(day_lbl,totals)):
            pct = max(h/mx*100, 4 if h>0 else 0)
            c   = COLS[i%len(COLS)]
            lbl = f"{h:.1f}h" if h>0 else "–"

            bars += f"""
            <div style="display:flex;flex-direction:column;align-items:center;gap:4px;flex:1;">
                <div style="font-family:'DM Mono',monospace;font-size:9px;color:var(--muted);">{lbl}</div>
                <div style="width:100%;border-radius:5px 5px 0 0;height:{pct}%;
                            background:{'linear-gradient(to top,'+c+','+c+'88)' if h>0 else 'var(--sur2)'};
                            min-height:{5 if h>0 else 2}px;border-radius:3px;"></div>
                <div style="font-family:'DM Mono',monospace;font-size:9px;color:var(--muted);">{d}</div>
            </div>"""

        chart = f'<div style="display:flex;align-items:flex-end;gap:8px;height:100px;padding-bottom:4px;">{bars}</div>'

        if not has_logs:
            chart = '<div class="empty"><div class="empty-ico">📊</div>Study hours will appear here after logging sessions.</div>'

        st.markdown(panel_open("Study Hours This Week","7 DAYS") + chart + panel_close(), unsafe_allow_html=True)