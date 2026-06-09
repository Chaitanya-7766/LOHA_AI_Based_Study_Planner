import streamlit as st
import plotly.graph_objects as go
import numpy as np
from datetime import date
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ml_engine import (init_models,predict_exam_score,detect_weak_subjects,
    recommend_study_times,detect_performance_trend,compute_spaced_repetition,
    compute_readiness_score)
from pages_loha.ui_helpers import page_header,stat_card,insight_card,COLS
import db

DIFFICULTY_MAP = {"critical":"beginner tutorial simply","weak":"step by step tutorial",
                  "moderate":"practice problems solved","strong":"advanced deep dive"}
CHANNELS = {"Machine Learning":["3Blue1Brown","StatQuest","Sentdex"],
            "Data Structures":["Abdul Bari","NeetCode","Back To Back SWE"],
            "Networks":["NetworkChuck","PowerCert Animated Videos"],
            "default":["Khan Academy","CrashCourse","MIT OpenCourseWare"]}

def section_header(title, tag=""):
    tag_html = f'<span class="ptag">{tag}</span>' if tag else ""
    st.markdown(
        f'<div class="panel" style="margin-bottom:10px;"><div class="ph">'
        f'<span class="ptitle">{title}</span>{tag_html}</div></div>',
        unsafe_allow_html=True,
    )

def build_recommendations(subjects, logs, exam_days):
    if not subjects:
        return [
            ("💡", "i", "Start With Setup", "Add your subjects, target scores, exam date, and daily study hours."),
            ("📅", "i", "Generate A Schedule", "Once subjects are added, LOHA can create your first weekly study plan."),
            ("⏱", "g", "Log Your First Session", "Use Focus Timer after studying so AI Insights can learn from your progress."),
        ]

    insights = []
    weak = []
    strong = []
    for s in subjects:
        sc, tgt = s.get("avg_score", 0), s.get("target_score", 80)
        if sc < tgt - 15:
            weak.append((s, sc, tgt))
        if sc >= 85:
            strong.append(s)

    for s, sc, tgt in weak[:3]:
        insights.append((
            "⚠️", "w", f"Weak Area: {s['name']}",
            f"Avg {round(sc)}% vs target {tgt}%. Add focused revision blocks this week.",
        ))

    if logs:
        avg = sum(s.get("avg_score", 0) for s in subjects) / max(len(subjects), 1)
        insights.append((
            "📊", "g", "Progress Data Found",
            f"{len(logs)} sessions logged. Current subject average is {avg:.0f}%.",
        ))
    else:
        insights.append((
            "⏱", "i", "No Sessions Logged Yet",
            "Start one Focus Timer session so LOHA can calculate trends and study consistency.",
        ))

    if strong:
        insights.append((
            "🔥", "g", f"Strong In {strong[0]['name']}",
            "You can maintain this subject while shifting more time to weaker areas.",
        ))

    if exam_days < 14:
        insights.append((
            "⏰", "w", "Exam Is Near",
            f"Only {exam_days} days left. Prioritize weak topics and revision over new material.",
        ))

    return insights or [
        ("📅", "i", "Schedule Ready", "Generate or refresh your weekly plan from the Schedule page."),
    ]

def show():
    subjects = st.session_state.get("subjects",[])
    profile  = st.session_state.get("profile",{})
    logs     = st.session_state.get("progress_log",[])

    exam_days = 30
    if profile.get("exam_date"):
        try:
            ed = date.fromisoformat(str(profile["exam_date"])[:10])
            exam_days = max(1,(ed-date.today()).days)
        except: pass

    st.title("AI Insights")
    st.caption("ML-powered analysis & predictions")
    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)

    with st.spinner("🔧 Loading ML models (GradientBoost · RandomForest · KMeans)..."):
        init_models()

    # ── Stat cards ───────────────────────────────────────────────────
    avg_score = sum(s.get("avg_score",0) for s in subjects)/len(subjects) if subjects else 0
    readiness = compute_readiness_score(subjects,min(len(logs),7),0.7,exam_days) if subjects else round(avg_score)
    pred_score = 0.0
    if subjects:
        cons = min(len(logs)/14,1.0)
        p = predict_exam_score(avg_score, min(len(logs),7)*1.5, exam_days, len(logs), cons,
                               float(profile.get("target_score",80)))
        pred_score = p["predicted_score"]
    peak_lbl = {"morning":"Morning","afternoon":"Afternoon","evening":"Evening","night":"Night"}.get(
        profile.get("peak_time","evening"),"Evening")

    cols = st.columns(4)
    cols[0].markdown(stat_card("🎯","Readiness Score",f"{readiness:.0f}%","sa",
        "On track 🎯" if readiness>=70 else "Needs work ⚠️"), unsafe_allow_html=True)
    cols[1].markdown(stat_card("📈","Predicted Score",f"{pred_score:.0f}%","sp","GradientBoost"), unsafe_allow_html=True)
    cols[2].markdown(stat_card("⏰","Peak Focus Time",peak_lbl,"sc","KMeans cluster"), unsafe_allow_html=True)
    cols[3].markdown(stat_card("📅","Days to Exam",exam_days,"sg"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 1: Weak Topics + Spaced Repetition ────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        section_header("🔬 ML Weak Topic Analysis","RANDOM FOREST")
        if st.button("🔬 Run Analysis", key="weak_run"):
            if not subjects: st.warning("Add subjects in Setup first.")
            else:
                with st.spinner("RandomForest analyzing..."):
                    st.session_state["weak_results"] = detect_weak_subjects(subjects)
        wr = st.session_state.get("weak_results",[])
        tc = {"strong":"#10b981","moderate":"#f59e0b","weak":"#ef4444","critical":"#7c3aed"}
        if wr:
            for r in wr:
                c   = tc.get(r["weakness_tier"],"#5a7090")
                ico = {"critical":"🚨","weak":"⚠️","moderate":"📊","strong":"✅"}.get(r["weakness_tier"],"💡")
                st.markdown(f"""
                <div class="ic" style="border-left:3px solid {c};">
                    <div class="icico" style="background:{c}22;">{ico}</div>
                    <div style="flex:1;">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <span class="ictxt"><strong>{r['name']}</strong></span>
                            <span style="font-size:9px;padding:2px 8px;border-radius:20px;background:{c}22;color:{c};border:1px solid {c}44;">{r['weakness_tier'].upper()}</span>
                        </div>
                        <div style="font-size:11px;color:var(--muted);margin-top:3px;">{r.get('recommendation','')[:100]}</div>
                        <div style="font-size:10px;color:var(--muted);">Avg: {r.get('avg_score',0):.0f}% → Target: {r.get('target_score',80):.0f}%</div>
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty"><div class="empty-ico">🔬</div>Click Run Analysis to detect weak topics.</div>', unsafe_allow_html=True)

    with c2:
        section_header("🔁 Spaced Repetition (SM-2)","DUE TODAY")
        if st.button("🔁 Compute SM-2 Schedule", key="sr_run"):
            if not subjects: st.warning("Add subjects first.")
            else:
                sr = []
                for s in subjects:
                    r = compute_spaced_repetition(s["name"],float(s.get("avg_score",60)),5,int(s.get("session_count",2)))
                    r["name"] = s["name"]; r["icon"] = s.get("icon","📚")
                    sr.append(r)
                sr.sort(key=lambda x:x["urgency_score"],reverse=True)
                st.session_state["sr_results"] = sr
        sr = st.session_state.get("sr_results",[])
        if sr:
            due = [s for s in sr if s["is_due"]]
            if due:
                st.markdown(f'<div style="color:#ef4444;font-size:12px;margin-bottom:8px;">🔴 {len(due)} subject(s) due today!</div>', unsafe_allow_html=True)
            for r in sr:
                uc = "#ef4444" if r["is_due"] else "#10b981"
                st.markdown(f"""
                <div class="ic" style="border-left:3px solid {uc};">
                    <div style="font-size:20px;">{r.get('icon','📚')}</div>
                    <div style="flex:1;">
                        <div style="display:flex;justify-content:space-between;">
                            <span class="ictxt"><strong>{r['name']}</strong></span>
                            <span style="color:{uc};font-size:11px;font-weight:700;">{'⚠️ DUE' if r['is_due'] else f"In {r['interval_days']}d"}</span>
                        </div>
                        <div style="font-size:10px;color:var(--muted);">{r['message']}</div>
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty"><div class="empty-ico">🔁</div>Click Compute SM-2 Schedule.</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 2: Score Predictions + Study Time ─────────────────────────
    c3, c4 = st.columns(2)
    with c3:
        section_header("📊 Exam Score Predictions","GRADIENT BOOST")
        if st.button("📊 Predict All Subjects", key="pred_all"):
            if not subjects: st.warning("Add subjects first.")
            else:
                cons = min(len(logs)/14,1.0)
                preds = []
                for s in subjects:
                    p = predict_exam_score(float(s.get("avg_score",60)),
                        float(profile.get("daily_hours",4))*7, exam_days, len(logs), cons,
                        float(s.get("target_score",80)))
                    p["name"]=s["name"]; p["icon"]=s.get("icon","📚"); p["color"]=s.get("color",COLS[0])
                    preds.append(p)
                preds.sort(key=lambda x:x["gap"],reverse=True)
                st.session_state["pred_results"] = preds
        pr = st.session_state.get("pred_results",[])
        if pr:
            for p in pr:
                bar_c = "#10b981" if p["on_track"] else "#ef4444"
                pct   = p["predicted_score"]
                st.markdown(f"""
                <div class="ic">
                    <div style="font-size:18px;">{p['icon']}</div>
                    <div style="flex:1;">
                        <div style="display:flex;justify-content:space-between;">
                            <span class="ictxt"><strong>{p['name']}</strong></span>
                            <span style="font-family:'DM Mono',monospace;font-size:13px;color:{bar_c};">{pct:.0f}%</span>
                        </div>
                        <div style="height:4px;background:var(--brd);border-radius:100px;overflow:hidden;margin:5px 0 3px;">
                            <div style="width:{pct}%;height:100%;background:{bar_c};border-radius:100px;"></div>
                        </div>
                        <div style="font-size:10px;color:var(--muted);">Target: {p['target_score']:.0f}% · {'✓ On track' if p['on_track'] else str(p['extra_hours_needed'])+'h needed'}</div>
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty"><div class="empty-ico">📊</div>Click Predict All Subjects.</div>', unsafe_allow_html=True)

    with c4:
        section_header("⏱ Optimal Study Windows","KMEANS")
        if st.button("⏱ Analyze Windows", key="kmeans_run"):
            sess_data = [{"started_at":l.get("date","")+" 19:00:00","duration_mins":60,
                          "focus_score":float(l.get("score",70))/10} for l in logs]
            with st.spinner("KMeans clustering..."):
                result = recommend_study_times(sess_data, float(profile.get("daily_hours",4)),
                                               profile.get("peak_time","evening"))
            st.session_state["study_time_result"] = result
        study_time_data = st.session_state.get("study_time_result")
        if study_time_data:
            st.markdown(
                insight_card(
                    "⏰",
                    f"Peak: {study_time_data['peak_label']}",
                    study_time_data["message"],
                    style="i"
                ),
                unsafe_allow_html=True
            )

            for slot in study_time_data.get("slots", []):
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:8px 12px;background:var(--sur2);border-radius:8px;margin-bottom:4px;">
                    <span style="font-family:'DM Mono',monospace;color:var(--acc);">
                        {slot['start']} – {slot['end']}
                    </span>
                    <span style="font-size:10px;color:var(--muted);">
                        {slot['duration_mins']} min
                    </span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty"><div class="empty-ico">⏱</div>Click Analyze Windows.</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Performance Trend (full width) ────────────────────────────────
    section_header("📉 Performance Trend","LINEAR REGRESSION")
    scores_str = st.text_input("Test scores (comma-separated, oldest→newest)",
                                "55, 60, 58, 65, 70, 68, 75", key="trend_inp")
    if st.button("📉 Analyze Trend", key="trend_run"):
        try:
            scores = [float(x.strip()) for x in scores_str.split(",") if x.strip()]
            result = detect_performance_trend(scores)
            tc2 = {"improving":"#10b981","declining":"#ef4444","stable":"#f59e0b"}.get(result["trend"],"#5a7090")
            c1,c2,c3,c4 = st.columns(4)
            c1.markdown(stat_card("📉","Trend",result['trend'].capitalize(),"sc"), unsafe_allow_html=True)
            c2.markdown(stat_card("🎯","Projected",f"{result['projected_next']}%","sp"), unsafe_allow_html=True)
            c3.markdown(stat_card("📊","Average",f"{result['avg_score']}%","sa"), unsafe_allow_html=True)
            c4.markdown(stat_card("📈","Slope",f"{result['slope']:+.1f}","sg"), unsafe_allow_html=True)
            st.markdown(f'<div class="ic" style="border-left:3px solid {tc2};margin-top:8px;"><div class="ictxt">{result["message"]}</div></div>', unsafe_allow_html=True)
            x = list(range(1,len(scores)+1))
            z = np.polyfit(x,scores,1); p = np.poly1d(z)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x,y=scores,mode="lines+markers",name="Actual",
                line=dict(color="#00d4ff",width=2),marker=dict(size=8,color="#00d4ff")))
            fig.add_trace(go.Scatter(x=x+[len(scores)+1],
                y=[p(i) for i in x]+[float(np.clip(p(len(scores)+1),0,100))],
                mode="lines",name="Trend",line=dict(color=tc2,width=1.5,dash="dash")))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(13,20,32,1)",
                font_color="#5a7090",height=220,
                xaxis=dict(gridcolor="rgba(30,45,69,1)",title="Test #"),
                yaxis=dict(gridcolor="rgba(30,45,69,1)",range=[0,105],title="Score %"),
                legend=dict(orientation="h"),margin=dict(t=10,b=10))
            st.plotly_chart(fig,use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── YouTube Resources ─────────────────────────────────────────────
    section_header("▶ YouTube Learning Resources")
    subj_names = [s["name"] for s in subjects] if subjects else ["Machine Learning"]
    yt_c1, yt_c2, yt_c3 = st.columns([2,2,1])
    yt_subj  = yt_c1.selectbox("Subject", subj_names, key="yt_subj_sel")
    yt_topic = yt_c2.text_input("Topic (optional)", key="yt_topic_inp", placeholder="e.g. Backpropagation")
    find_yt  = yt_c3.button("🔍 Find", key="yt_find")
    if find_yt:
        wr = st.session_state.get("weak_results",[])
        tier = next((r.get("weakness_tier","moderate") for r in wr if r.get("name")==yt_subj), "moderate")
        q    = f"{yt_subj} {yt_topic} {DIFFICULTY_MAP.get(tier,'tutorial')}".strip()
        chs  = CHANNELS.get(yt_subj, CHANNELS["default"])
        tc3  = {"critical":"#7c3aed","weak":"#ef4444","moderate":"#f59e0b","strong":"#10b981"}.get(tier,"#5a7090")
        st.markdown(f'<div style="background:var(--sur2);border-radius:8px;padding:10px 13px;margin-bottom:10px;font-size:11px;color:var(--muted);">ML Query ({tier}): <span style="color:var(--acc);font-style:italic;">{q}</span></div>', unsafe_allow_html=True)
        url = "https://www.youtube.com/results?search_query=" + q.replace(" ","+")
        st.markdown(f'<a href="{url}" target="_blank" style="text-decoration:none;"><div class="ic" style="border-left:3px solid {tc3};cursor:pointer;"><div style="font-size:20px;">▶️</div><div><div class="ictxt"><strong>Search: {q}</strong></div><div style="font-size:10px;color:var(--muted);">YouTube · {tier} level</div></div></div></a>', unsafe_allow_html=True)
        for ch in chs:
            ch_url = f"https://www.youtube.com/results?search_query={ch}+{yt_subj}".replace(" ","+")
            st.markdown(f'<a href="{ch_url}" target="_blank" style="text-decoration:none;"><div class="ic" style="cursor:pointer;"><div style="font-size:18px;">📺</div><div><div class="ictxt"><strong>{ch}</strong></div><div style="font-size:10px;color:var(--muted);">Recommended for {yt_subj}</div></div></div></a>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty"><div class="empty-ico">▶</div>Select a subject and click Find.</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── AI Recommendations ────────────────────────────────────────────
    section_header("🧠 AI Recommendations")
    if st.button("🔄 Refresh Insights", key="refresh_ins"):
        ins = build_recommendations(subjects, logs, exam_days)
        st.session_state["ai_ins"] = ins
        try:
            for ico,style,title,body in ins:
                db.save_chat({"role":"assistant","message":f"{title}: {body}"})
        except: pass
    ins = st.session_state.get("ai_ins") or build_recommendations(subjects, logs, exam_days)
    for ico, style, title, body in ins:
        st.info(f"{title}\n\n{body}")


def show_time_analysis():
    """Called from ai_insights to show time vs target ML analysis."""
    from ml_engine import analyze_time_vs_target
    logs = st.session_state.get("progress_log", [])
    if not logs:
        st.markdown('<div class="empty"><div class="empty-ico">⏱️</div>Log study sessions in Focus Timer first.</div>', unsafe_allow_html=True)
        return

    results = analyze_time_vs_target(logs)
    if not results:
        st.markdown('<div class="empty"><div class="empty-ico">⏱️</div>No subject data found.</div>', unsafe_allow_html=True)
        return

    for r in results:
        bar_c   = "#10b981" if r["enough"] else ("#f59e0b" if r["gap_hrs"] < 2 else "#ef4444")
        trend   = f"📈 +{r['slope']:.1f}pts/session" if r["slope"] > 0 else (f"📉 {r['slope']:.1f}pts/session" if r["slope"] < 0 else "➡️ Stable")
        st.markdown(f"""
        <div class="ic" style="border-left:3px solid {bar_c};flex-direction:column;align-items:stretch;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                <span class="ictxt"><strong>{r['subject']}</strong>
                    <span style="font-size:10px;color:var(--muted);margin-left:8px;">{r['sessions']} sessions · {trend}</span>
                </span>
                <span style="font-size:11px;color:{bar_c};font-weight:700;">
                    {"✅ Enough" if r['enough'] else f"⚠️ Need {r['gap_hrs']}h more"}
                </span>
            </div>
            <div style="display:flex;gap:16px;margin-bottom:8px;">
                <span style="font-size:11px;color:var(--muted);">Spent: <b style="color:{bar_c};">{r['total_hrs']}h</b></span>
                <span style="font-size:11px;color:var(--muted);">Required: <b style="color:var(--txt);">{r['required_hrs']}h</b></span>
                <span style="font-size:11px;color:var(--muted);">Avg: <b style="color:var(--acc);">{r['avg_score']}%</b></span>
                <span style="font-size:11px;color:var(--muted);">Target: <b style="color:var(--acc3);">{r['target_score']:.0f}%</b></span>
            </div>
            <div style="height:4px;background:var(--sur);border-radius:100px;overflow:hidden;margin-bottom:5px;">
                <div style="width:{r['pct_done']}%;height:100%;background:{bar_c};border-radius:100px;"></div>
            </div>
            <div style="font-size:10px;color:var(--muted);">🤖 {r['recommendation']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Time vs Target ML Analysis ──────────────────────────────────
    section_header("⏱️ Time Spent vs Target Score Analysis","ML ENGINE")
    from ml_engine import analyze_time_vs_target
    logs_for_time = st.session_state.get("progress_log",[])
    time_results  = analyze_time_vs_target(logs_for_time) if logs_for_time else []
    if time_results:
        for r in time_results:
            bar_c = "#10b981" if r["enough"] else ("#f59e0b" if r["gap_hrs"] < 2 else "#ef4444")
            trend = f"📈 +{r['slope']:.1f}pts" if r["slope"]>0 else (f"📉 {r['slope']:.1f}pts" if r["slope"]<0 else "➡️ Stable")
            st.markdown(f"""
            <div class="ic" style="border-left:3px solid {bar_c};flex-direction:column;align-items:stretch;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                    <span class="ictxt"><strong>{r['subject']}</strong>
                        <span style="font-size:10px;color:var(--muted);margin-left:8px;">{r['sessions']} sessions · {trend}</span>
                    </span>
                    <span style="font-size:11px;color:{bar_c};font-weight:700;">
                        {"✅ Enough" if r["enough"] else f"⚠️ Need {r['gap_hrs']}h more"}
                    </span>
                </div>
                <div style="display:flex;gap:16px;margin-bottom:8px;">
                    <span style="font-size:11px;color:var(--muted);">Spent: <b style="color:{bar_c};">{r["total_hrs"]}h</b></span>
                    <span style="font-size:11px;color:var(--muted);">Required: <b style="color:var(--txt);">{r["required_hrs"]}h</b></span>
                    <span style="font-size:11px;color:var(--muted);">Avg: <b style="color:var(--acc);">{r["avg_score"]}%</b></span>
                    <span style="font-size:11px;color:var(--muted);">Target: <b style="color:var(--acc3);">{r["target_score"]:.0f}%</b></span>
                </div>
                <div style="height:4px;background:var(--sur);border-radius:100px;overflow:hidden;margin-bottom:5px;">
                    <div style="width:{r["pct_done"]}%;height:100%;background:{bar_c};border-radius:100px;"></div>
                </div>
                <div style="font-size:10px;color:var(--muted);">🤖 {r["recommendation"]}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("<div class='empty'><div class='empty-ico'>⏱️</div>Log sessions with duration in Focus Timer to see time analysis.</div>", unsafe_allow_html=True)
