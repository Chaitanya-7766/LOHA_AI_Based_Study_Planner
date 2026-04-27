import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import json, sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ml_engine import estimate_difficulty, generate_schedule
from pages_loha.ui_helpers import page_header, COLS
import db

def show():
    profile  = st.session_state.get("profile", {})
    subjects = st.session_state.get("subjects", [])

    exam_days = None
    if profile.get("exam_date"):
        try: exam_days = max(0,(date.fromisoformat(profile["exam_date"])-date.today()).days)
        except: pass

    st.markdown(page_header("Study Schedule", "AI-Generated Study Schedule", exam_days), unsafe_allow_html=True)
    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)

    if "week_offset" not in st.session_state:
        st.session_state.week_offset = 0
    if "schedule_slots" not in st.session_state:
        st.session_state.schedule_slots = []

    wk_start = date.today() - timedelta(days=date.today().weekday()) + timedelta(weeks=st.session_state.week_offset)
    wk_end   = wk_start + timedelta(days=6)
    wk_label = f"{wk_start.strftime('%b %d')} – {wk_end.strftime('%b %d')}"

    # Navigation bar
    st.markdown(f"""
    <div class='panel'>
        <div class='ph'>
            <span class='ptitle'>AI-Generated Study Schedule</span>
            <span class='ptag'>{wk_label}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    nav1, nav2, nav3, nav4 = st.columns([1,2,1,2])
    if nav1.button("← Prev", key="s_prev"):
        st.session_state.week_offset -= 1; st.rerun()
    nav2.markdown(f"<div style='font-family:\"DM Mono\",monospace;font-size:11px;color:var(--muted);padding:10px 0;text-align:center;'>{wk_label}</div>", unsafe_allow_html=True)
    if nav3.button("Next →", key="s_next"):
        st.session_state.week_offset += 1; st.rerun()
    gen = nav4.button("✨ Generate Schedule", key="gen_btn")

    if gen:
        if not subjects:
            st.error("⚠ Add subjects in Setup first.")
        else:
            with st.spinner("✨ AI generating your schedule..."):
                enriched = [{**s,"subject_id":s.get("name"),"weakness_score":max(0,int((s.get("target_score",80)-s.get("avg_score",60))/20))} for s in subjects]
                slots = generate_schedule(
                    subjects=enriched, start_date=wk_start, end_date=wk_end,
                    daily_hours=float(profile.get("daily_hours",4)),
                    peak_time=profile.get("peak_time","evening"),
                )
                subj_map = {s["name"]:s for s in subjects}
                for slot in slots:
                    sn = slot.get("subject_name","")
                    si = subj_map.get(sn,{})
                    slot["subjects"] = {"name":sn,"icon":si.get("icon","📚"),"color":si.get("color",COLS[0])}
                st.session_state.schedule_slots = slots
            st.success(f"✨ Generated {len(slots)} slots!")

    # Render schedule
    today = date.today().strftime("%Y-%m-%d")
    week_slots = [s for s in st.session_state.schedule_slots
                  if wk_start.strftime("%Y-%m-%d") <= s.get("slot_date","") <= wk_end.strftime("%Y-%m-%d")]

    if not week_slots:
        sched_html = "<div class='empty'><div class='empty-ico'>📅</div>No schedule yet. Click \"Generate Schedule\" above.</div>"
    else:
        from collections import defaultdict
        grouped = defaultdict(list)
        for s in week_slots: grouped[s["slot_date"]].append(s)
        sched_html = ""
        for ds, day_slots in sorted(grouped.items()):
            try: lbl = datetime.strptime(ds,"%Y-%m-%d").strftime("%A, %b %d")
            except: lbl = ds
            is_today = ds == today
            sched_html += f"<div style='margin-bottom:16px'><div class='dlbl'>{lbl}{'<span class=\"tbadge\">TODAY</span>' if is_today else ''}</div>"
            for sl in day_slots:
                subj = sl.get("subjects",{})
                c    = subj.get("color") or sl.get("subject_color","#00d4ff")
                st_t = (sl.get("start_time","") or "")[:5]
                et_t = (sl.get("end_time","")   or "")[:5]
                status = sl.get("status","scheduled")
                stc  = "#10b981" if status=="done" else ("#f59e0b" if status=="pending" else "#5a7090")
                name = subj.get("name") or sl.get("subject_name","Study")
                icon = subj.get("icon") or sl.get("subject_icon","📚")
                sched_html += f"<div class='sslot'><span class='stime'>{st_t} – {et_t}</span><div class='sbar' style='border-color:{c}'><span class='ssub'>{icon} {name}</span><div style='display:flex;align-items:center;gap:5px;'><span class='stag2' style='background:{stc}22;color:{stc}'>{status.upper()}</span></div></div></div>"
            sched_html += "</div>"

    st.markdown(f"<div class='panel'><div class='pb'>{sched_html}</div></div>", unsafe_allow_html=True)

    if week_slots:
        rows = [{"Date":s["slot_date"],"Subject":s.get("subject_name",""),"Start":s.get("start_time",""),"End":s.get("end_time",""),"Status":s.get("status","")} for s in week_slots]
        st.download_button("⬇️ Export CSV", pd.DataFrame(rows).to_csv(index=False), "loha_schedule.csv", "text/csv")
