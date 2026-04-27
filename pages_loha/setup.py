import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pages_loha.ui_helpers import page_header, section_header, COLS
import db

def show():
    st.title("Setup")
    st.caption("Configure your study profile & subjects")
    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)
    if "profile" not in st.session_state: st.session_state.profile = {}
    if "subjects" not in st.session_state: st.session_state.subjects = []
    prof = st.session_state.profile

    st.markdown(section_header("Your Study Profile", "PERSONALISE"), unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    p_name   = c1.text_input("Full Name", prof.get("full_name",""), placeholder="e.g. Chaitanya", key="p_name")
    p_hours  = c2.number_input("Daily Study Hours", 1,16, int(prof.get("daily_hours",4)), key="p_hours")
    c3,c4 = st.columns(2)
    p_target = c3.number_input("Target Score %", 0,100, int(prof.get("target_score",80)), key="p_target")
    p_exam   = c4.date_input("Exam Date", key="p_exam")
    c5,c6 = st.columns(2)
    peak_opts = ["morning","afternoon","evening","night"]
    peak_lbls = ["Morning (6AM–10AM)","Afternoon (12PM–4PM)","Evening (8PM–11PM)","Late Night (11PM–2AM)"]
    pidx = peak_opts.index(prof.get("peak_time","evening"))
    p_peak  = c5.selectbox("Peak Study Time", peak_lbls, index=pidx, key="p_peak")
    p_style = c6.selectbox("Learning Style", ["Visual","Practice problems","Read & revise","Flashcards"], index=1, key="p_style")
    if st.button("💾 Save Profile", key="save_prof"):
        st.session_state.profile = {"full_name":p_name,"daily_hours":p_hours,"target_score":p_target,"exam_date":str(p_exam),"peak_time":peak_opts[peak_lbls.index(p_peak)],"learning_style":p_style}
        st.success("✓ Profile saved!")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(section_header("Subjects", "MANAGE"), unsafe_allow_html=True)
    subjects = st.session_state.subjects
    # Chips
    if subjects:
        chips = "".join([f"<span class='chip' style='border-color:{s.get('color',COLS[i%len(COLS)])}55'><span style='color:{s.get('color',COLS[i%len(COLS)])}'>{s.get('icon','📚')} {s['name']}</span></span>" for i,s in enumerate(subjects)])
        st.markdown(chips, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns([3,1,1,1])
    ns_name   = c1.text_input("Subject Name", placeholder="e.g. Physics", key="setup_ns")
    ns_icon   = c2.text_input("Emoji", "📚", key="setup_ic")
    ns_target = c3.number_input("Target %", 50,100,80, key="setup_tgt")
    ns_avg    = c4.number_input("Current %", 0,100,60, key="setup_avg")
    if st.button("+ Add Subject", key="setup_add"):
        if ns_name:
            new_s = {"name":ns_name,"icon":ns_icon or "📚","target_score":int(ns_target),"avg_score":float(ns_avg),"color":COLS[len(subjects)%len(COLS)],"session_count":0,"test_count":0,"topics":"—"}
            st.session_state.subjects.append(new_s)
            try:
                db.save_subject(new_s)
            except:
                pass
            st.success(f"✓ {ns_name} added!"); st.rerun()
        else: st.warning("Enter a subject name.")

    if subjects:
        st.markdown("<br><div style='font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>Remove:</div>", unsafe_allow_html=True)
        for i,s in enumerate(subjects):
            c = s.get("color",COLS[i%len(COLS)])
            col1,col2 = st.columns([5,1])
            col1.markdown(f"<span style='color:{c};font-size:13px;'>{s.get('icon','📚')} {s['name']} — Avg:{round(s.get('avg_score',0))}% Target:{s.get('target_score',80)}%</span>", unsafe_allow_html=True)
            if col2.button("✕", key=f"sdel_{i}"):
                try: db.delete_subject(subjects[i]["name"])
                except: pass
                st.session_state.subjects.pop(i); st.rerun()
