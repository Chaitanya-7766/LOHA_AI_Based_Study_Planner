import streamlit as st
import plotly.graph_objects as go
import numpy as np
from datetime import date
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ml_engine import (init_models, predict_exam_score, detect_weak_subjects,
    recommend_study_times, detect_performance_trend, compute_spaced_repetition,
    compute_readiness_score)
from pages_loha.ui_helpers import page_header, stat_card, section_header, COLS

TIER_COLORS = {"strong":"#10b981","moderate":"#f59e0b","weak":"#ef4444","critical":"#7c3aed"}
TIER_ICONS  = {"strong":"ok","weak":"warning","moderate":"info","critical":"critical"}

def show():
    subjects = st.session_state.get("subjects", [])
    profile  = st.session_state.get("profile", {})
    logs     = st.session_state.get("progress_log", [])

    exam_days = 30
    if profile.get("exam_date"):
        try:
            exam_days = max(1, (date.fromisoformat(profile["exam_date"]) - date.today()).days)
        except:
            pass

    st.markdown(page_header("AI Insights",
                "5 ML models: Score Predictor · Weak Topics · Study Time · Trend · Spaced Repetition",
                exam_days), unsafe_allow_html=True)
    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)

    with st.spinner("Loading ML models (GradientBoosting, RandomForest, KMeans)..."):
        init_models()

    avg_s     = sum(s.get("avg_score", 0) for s in subjects) / len(subjects) if subjects else 0
    readiness = compute_readiness_score(subjects, min(len(logs), 7), 0.7, exam_days) if subjects else avg_s
    peak_map  = {"morning": "Morning", "afternoon": "Afternoon", "evening": "Evening", "night": "Night"}
    pred_score = 0.0
    if subjects:
        p = predict_exam_score(avg_s, min(len(logs), 7) * 1.5, exam_days, len(logs),
                               min(len(logs) / 14, 1.0), float(profile.get("target_score", 80)))
        pred_score = p["predicted_score"]

    cards = "".join([
        stat_card("🎯", "Readiness Score", f"{readiness:.0f}%", "sa"),
        stat_card("📈", "Predicted Score",  f"{pred_score:.0f}%", "sp", "GradientBoost"),
        stat_card("⏰", "Peak Focus", peak_map.get(profile.get("peak_time", "evening"), "Evening"), "sc", "KMeans"),
        stat_card("📅", "Days to Exam", exam_days, "sg"),
    ])
    st.markdown(f"<div class='cgrid'>{cards}</div>", unsafe_allow_html=True)

    # ── Row 1: Weak Topics + Spaced Repetition ───────────────────────
    c1, c2 = st.columns(2)

    with c1:
        st.markdown(section_header("ML Weak Topic Analysis", "RANDOM FOREST"), unsafe_allow_html=True)
        if st.button("Run Weak Analysis", key="ml_weak_run"):
            if not subjects:
                st.warning("Add subjects in Setup first.")
            else:
                with st.spinner("RandomForest analyzing..."):
                    results = detect_weak_subjects(subjects)
                st.session_state["weak_results"] = results

        for r in st.session_state.get("weak_results", []):
            tier  = r.get("weakness_tier", "moderate")
            color = TIER_COLORS.get(tier, "#5a7090")
            icon  = "Critical" if tier == "critical" else ("Weak" if tier == "weak" else ("OK" if tier == "strong" else "Moderate"))
            name  = r.get("name", "")
            rec   = r.get("recommendation", "")[:90]
            avg_v = r.get("avg_score", 0)
            tgt_v = r.get("target_score", 80)
            st.markdown(
                f"<div class='ic' style='border-left:3px solid {color};'>"
                f"<div style='flex:1;'>"
                f"<div style='display:flex;justify-content:space-between;'>"
                f"<span class='ictxt'><strong>{name}</strong></span>"
                f"<span style='font-size:9px;padding:2px 8px;border-radius:20px;"
                f"background:{color}22;color:{color};border:1px solid {color}44;'>{tier.upper()}</span>"
                f"</div>"
                f"<div style='font-size:11px;color:var(--muted);margin-top:3px;'>{rec}</div>"
                f"<div style='font-size:10px;color:var(--muted);'>Avg:{avg_v:.0f}% Target:{tgt_v:.0f}%</div>"
                f"</div></div>",
                unsafe_allow_html=True
            )
        if not st.session_state.get("weak_results"):
            st.markdown("<div class='empty'><div class='empty-ico'>🔬</div>Click Run Analysis.</div>", unsafe_allow_html=True)

    with c2:
        st.markdown(section_header("Spaced Repetition (SM-2)", "DUE TODAY"), unsafe_allow_html=True)
        if st.button("Compute SM-2 Schedule", key="sr_run"):
            if not subjects:
                st.warning("Add subjects first.")
            else:
                sr = []
                for s in subjects:
                    rep = compute_spaced_repetition(
                        s["name"], float(s.get("avg_score", 60)), 5, int(s.get("session_count", 2))
                    )
                    rep["name"] = s["name"]
                    rep["icon"] = s.get("icon", "📚")
                    sr.append(rep)
                sr.sort(key=lambda x: x["urgency_score"], reverse=True)
                st.session_state["sr_results"] = sr

        for r in st.session_state.get("sr_results", []):
            uc       = "#ef4444" if r["is_due"] else "#10b981"
            due_txt  = "DUE TODAY" if r["is_due"] else ("In " + str(r["interval_days"]) + "d")
            icon_txt = r.get("icon", "📚")
            name_txt = r.get("name", "")
            msg_txt  = r.get("message", "")
            st.markdown(
                f"<div class='ic' style='border-left:3px solid {uc};'>"
                f"<div style='font-size:18px;'>{icon_txt}</div>"
                f"<div style='flex:1;'>"
                f"<div style='display:flex;justify-content:space-between;'>"
                f"<span class='ictxt'><strong>{name_txt}</strong></span>"
                f"<span style='color:{uc};font-size:11px;font-weight:700;'>{due_txt}</span>"
                f"</div>"
                f"<div style='font-size:10px;color:var(--muted);'>{msg_txt}</div>"
                f"</div></div>",
                unsafe_allow_html=True
            )
        if not st.session_state.get("sr_results"):
            st.markdown("<div class='empty'><div class='empty-ico'>🔁</div>Click Compute Schedule.</div>", unsafe_allow_html=True)

    # ── Row 2: Exam Predictions + Study Windows ──────────────────────
    c3, c4 = st.columns(2)

    with c3:
        st.markdown(section_header("📊 Exam Score Predictions", "GRADIENT BOOST"), unsafe_allow_html=True)
        if st.button("Predict Exam Scores", key="pred_run"):
            if not subjects:
                st.warning("Add subjects first.")
            else:
                cons  = min(len(logs) / 14, 1.0)
                preds = []
                for i, s in enumerate(subjects):
                    p = predict_exam_score(
                        float(s.get("avg_score", 60)),
                        float(profile.get("daily_hours", 4)) * 7,
                        exam_days, len(logs), cons,
                        float(s.get("target_score", 80))
                    )
                    p["name"]  = s["name"]
                    p["icon"]  = s.get("icon", "📚")
                    p["color"] = s.get("color", COLS[i % len(COLS)])
                    preds.append(p)
                preds.sort(key=lambda x: x["gap"], reverse=True)
                st.session_state["pred_results"] = preds

        for p in st.session_state.get("pred_results", []):
            bar_c    = "#10b981" if p["on_track"] else "#ef4444"
            ps       = p["predicted_score"]
            tgt      = p["target_score"]
            extra    = p["extra_hours_needed"]
            on_track = p["on_track"]
            status   = "On track" if on_track else (str(extra) + "h needed")
            st.markdown(
                f"<div class='ic'>"
                f"<div style='font-size:18px;'>{p['icon']}</div>"
                f"<div style='flex:1;'>"
                f"<div style='display:flex;justify-content:space-between;'>"
                f"<span class='ictxt'><strong>{p['name']}</strong></span>"
                f"<span style='font-family:\"DM Mono\",monospace;font-size:13px;color:{bar_c};'>{ps:.0f}%</span>"
                f"</div>"
                f"<div style='height:4px;background:var(--brd);border-radius:100px;overflow:hidden;margin:5px 0 3px;'>"
                f"<div style='width:{ps}%;height:100%;background:{bar_c};border-radius:100px;'></div></div>"
                f"<div style='font-size:10px;color:var(--muted);'>Target:{tgt:.0f}% · {status}</div>"
                f"</div></div>",
                unsafe_allow_html=True
            )
        if not st.session_state.get("pred_results"):
            st.markdown("<div class='empty'><div class='empty-ico'>📊</div>Click Predict Scores.</div>", unsafe_allow_html=True)

    with c4:
        st.markdown(section_header("⏱ Optimal Study Windows", "KMEANS"), unsafe_allow_html=True)
        if st.button("Analyze Study Windows", key="km_run"):
            sess_d = [{"started_at": l.get("date", "") + " 19:00:00",
                       "duration_mins": 60,
                       "focus_score": float(l.get("score", 70)) / 10}
                      for l in logs]
            with st.spinner("KMeans clustering..."):
                result = recommend_study_times(
                    sess_d,
                    float(profile.get("daily_hours", 4)),
                    profile.get("peak_time", "evening")
                )
            st.session_state["st_result"] = result

        st_res = st.session_state.get("st_result")
        if st_res:
            peak_lbl = st_res.get("peak_label", "")
            msg      = st_res.get("message", "")
            st.markdown(
                f"<div class='ic' style='border-left:3px solid var(--acc);'>"
                f"<div class='icico icico-i'>⏰</div>"
                f"<div><div class='ictxt'><strong>Peak: {peak_lbl}</strong></div>"
                f"<div style='font-size:11px;color:var(--muted);margin-top:3px;'>{msg}</div></div></div>",
                unsafe_allow_html=True
            )
            for slot in st_res.get("slots", []):
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;align-items:center;"
                    f"padding:8px 12px;background:var(--sur2);border-radius:8px;margin-bottom:4px;'>"
                    f"<span style='font-family:\"DM Mono\",monospace;color:var(--acc);'>"
                    f"{slot['start']} – {slot['end']}</span>"
                    f"<span style='font-size:10px;color:var(--muted);'>{slot['duration_mins']} min</span></div>",
                    unsafe_allow_html=True
                )
        else:
            st.markdown("<div class='empty'><div class='empty-ico'>⏱</div>Click Analyze Windows.</div>", unsafe_allow_html=True)

    # ── Performance Trend (full width) ──────────────────────────────
    st.markdown(section_header("📉 Performance Trend", "LINEAR REGRESSION"), unsafe_allow_html=True)
    scores_str = st.text_input("Enter test scores (comma-separated, oldest to newest)",
                                "55, 60, 58, 65, 70, 68, 75", key="ti_scores")
    if st.button("Analyze Performance Trend", key="trend_run", use_container_width=True):
        try:
            scores = [float(x.strip()) for x in scores_str.split(",") if x.strip()]
            result = detect_performance_trend(scores)
            tc2    = {"improving": "#10b981", "declining": "#ef4444", "stable": "#f59e0b"}.get(result["trend"], "#5a7090")
            cards2 = "".join([
                stat_card("📉", "Trend",     result["trend"].capitalize(), "sc"),
                stat_card("🎯", "Projected", f"{result['projected_next']}%", "sp"),
                stat_card("📊", "Average",   f"{result['avg_score']}%", "sa"),
                stat_card("↗",  "Slope",     f"{result['slope']:+.1f}", "sg"),
            ])
            st.markdown(f"<div class='cgrid'>{cards2}</div>", unsafe_allow_html=True)
            xv  = list(range(1, len(scores) + 1))
            z   = np.polyfit(xv, scores, 1)
            p   = np.poly1d(z)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=xv, y=scores, mode="lines+markers", name="Actual",
                                     line=dict(color="#00d4ff", width=2), marker=dict(size=8)))
            proj_x = len(scores) + 1
            proj_y = float(np.clip(p(proj_x), 0, 100))
            fig.add_trace(go.Scatter(x=xv + [proj_x], y=[p(i) for i in xv] + [proj_y],
                                     mode="lines", name="Trend",
                                     line=dict(color=tc2, width=1.5, dash="dash")))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,20,32,1)",
                font_color="#5a7090",
                xaxis=dict(gridcolor="rgba(30,45,69,1)", title="Test #"),
                yaxis=dict(gridcolor="rgba(30,45,69,1)", range=[0, 105], title="Score %"),
                legend=dict(orientation="h"), margin=dict(t=10, b=10), height=220
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.markdown("<div class='empty'><div class='empty-ico'>📉</div>Enter scores and click Analyze Trend.</div>", unsafe_allow_html=True)
