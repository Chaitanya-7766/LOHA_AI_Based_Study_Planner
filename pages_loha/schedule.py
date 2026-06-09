import streamlit as st
import pandas as pd
from datetime import date, timedelta
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ml_engine import estimate_difficulty, generate_schedule
from pages_loha.ui_helpers import panel_open, panel_close, schedule_slots_html, COLS
import db


def show():
    profile  = st.session_state.get("profile", {})
    subjects = st.session_state.get("subjects", [])

    # ── CLEAN HEADER (FIXED) ───────────────────────────────
    st.title("Schedule")
    st.caption("AI-Generated Study Schedule")
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ── SESSION STATE ──────────────────────────────────────
    if "week_offset" not in st.session_state:
        st.session_state.week_offset = 0
    if "schedule_slots" not in st.session_state:
        st.session_state.schedule_slots = []

    wk_start = date.today() - timedelta(days=date.today().weekday()) + timedelta(weeks=st.session_state.week_offset)
    wk_end   = wk_start + timedelta(days=6)
    wk_label = f"{wk_start.strftime('%b %d')} – {wk_end.strftime('%b %d')}"

    # ── NAV BAR ────────────────────────────────────────────
    c_prev, c_lbl, c_next, c_gen = st.columns([1, 2, 1, 2])

    if c_prev.button("← Prev", key="sched_prev"):
        st.session_state.week_offset -= 1
        st.rerun()

    c_lbl.markdown(
        f"<div style='font-family:\"DM Mono\",monospace;font-size:11px;color:var(--muted);padding:10px 0;text-align:center;'>{wk_label}</div>",
        unsafe_allow_html=True
    )

    if c_next.button("Next →", key="sched_next"):
        st.session_state.week_offset += 1
        st.rerun()

    gen = c_gen.button("✨ Generate Schedule", key="gen_sched")

    # ── GENERATE SCHEDULE ─────────────────────────────────
    if gen:
        if not subjects:
            st.error("Add subjects in Setup first.")
        else:
            with st.spinner("✨ AI generating your schedule..."):

                enriched = [{
                    **s,
                    "subject_id": s["name"],
                    "weakness_score": max(0, int((s.get("target_score",80)-s.get("avg_score",60))/20))
                } for s in subjects]

                slots = generate_schedule(
                    subjects=enriched,
                    start_date=wk_start,
                    end_date=wk_end,
                    daily_hours=float(profile.get("daily_hours",4)),
                    peak_time=profile.get("peak_time","evening"),
                )

                subj_map = {s["name"]: s for s in subjects}

                for slot in slots:
                    sname = slot.get("subject_name","")
                    info  = subj_map.get(sname,{})
                    slot["subjects"] = {
                        "name": sname,
                        "icon": info.get("icon","📚"),
                        "color": info.get("color", COLS[0])
                    }

                # replace only current week
                other = [
                    s for s in st.session_state.schedule_slots
                    if not (wk_start.strftime("%Y-%m-%d") <= s.get("slot_date","") <= wk_end.strftime("%Y-%m-%d"))
                ]

                st.session_state.schedule_slots = other + slots

                try:
                    db.save_schedule_slots(slots)
                except:
                    pass

            st.success(f"✨ Generated {len(slots)} slots for {wk_label}!")

    # ── FILTER WEEK DATA ──────────────────────────────────
    week_slots = [
        s for s in st.session_state.schedule_slots
        if wk_start.strftime("%Y-%m-%d") <= s.get("slot_date","") <= wk_end.strftime("%Y-%m-%d")
    ]

    # ── RENDER PANEL ──────────────────────────────────────
    sched_html = schedule_slots_html(week_slots)

    st.markdown(
        panel_open("AI-Generated Study Schedule", wk_label)
        + sched_html
        + panel_close(),
        unsafe_allow_html=True
    )

    # ── EXPORT ────────────────────────────────────────────
    if week_slots:
        rows = [{
            "Date": s["slot_date"],
            "Subject": s.get("subject_name",""),
            "Start": s.get("start_time",""),
            "End": s.get("end_time",""),
            "Status": s.get("status","scheduled")
        } for s in week_slots]

        st.download_button(
            "⬇️ Export CSV",
            pd.DataFrame(rows).to_csv(index=False),
            "loha_schedule.csv",
            "text/csv"
        )

    # ── LOAD PAST PLANS ───────────────────────────────────
    if st.button("📂 Load Past Plans", key="load_plans"):
        try:
            plans = db.get_all_plans()
            if plans:
                st.dataframe(
                    pd.DataFrame(plans)[["student_name","exam_date","daily_hours","created_at"]],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No past plans found.")
        except:
            st.info("ℹ️ Supabase not configured.")