import streamlit as st
import sys, os
import db as db_module

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from pages_loha.ui_helpers import COLS, ICOS, section_header


def show():
    # ── CLEAN HEADER (FIXED) ─────────────────────────────
    st.title("Subjects")
    st.caption("Your subject tracker & performance overview")
    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)

    if "subjects" not in st.session_state:
        st.session_state.subjects = []

    subjects = st.session_state.subjects

    # ── WEAK WARNINGS (UNCHANGED) ────────────────────────
    for s in subjects:
        if (s.get("avg_score",0)) < 60:
            st.markdown(
                f"<div class='wa'><div style='font-size:17px'>⚠️</div>"
                f"<div><strong>{s['name']}</strong> is a weak area — avg {round(s.get('avg_score',0))}%. "
                f"LOHA has boosted {s['name']} time in your schedule.</div></div>",
                unsafe_allow_html=True
            )

    # ── SUBJECT GRID (UNCHANGED) ─────────────────────────
    if subjects:
        grid = ""
        for i, s in enumerate(subjects):
            c  = s.get("color") or COLS[i % len(COLS)]
            sc = round(s.get("avg_score",0))
            sc_col = "#ef4444" if sc < 60 else c

            grid += f"""
            <div class='scrd' style='border-color:{c}44'>
                <div style='font-size:20px;margin-bottom:7px'>{s.get('icon',ICOS[i%len(ICOS)])}</div>
                <div style='font-family:Syne;font-size:13px;font-weight:700;color:{c};margin-bottom:2px'>{s['name']}</div>
                <div style='font-size:10px;color:var(--muted);margin-bottom:8px'>{s.get('topics','–')}</div>

                <div class='scbar'>
                    <div class='scfill' style='width:{sc}%;background:linear-gradient(90deg,{c},{c}77)'></div>
                </div>

                <div style='display:flex;gap:8px;font-size:10px;color:var(--muted);'>
                    <span>Score:<strong style='color:{sc_col}'> {sc}%</strong></span>
                    <span>Sessions:<strong style='color:var(--txt)'> {s.get('session_count',0)}</strong></span>
                    <span>Tests:<strong style='color:var(--txt)'> {s.get('test_count',0)}</strong></span>
                </div>
            </div>
            """

        grid += """
        <div class='scrd' style='border:2px dashed var(--brd);display:flex;flex-direction:column;align-items:center;justify-content:center;opacity:.5;'>
            <div style='font-size:24px;margin-bottom:5px'>+</div>
            <div style='font-size:12px;color:var(--muted)'>Add Subject</div>
        </div>
        """

        st.write("")  # spacer

        cols = st.columns(3)

        for i, s in enumerate(subjects):
            with cols[i % 3]:
                st.markdown(f"""
                **{s.get('icon','📚')} {s['name']}**
                
                Score: {round(s.get('avg_score',0))}%
                
                Sessions: {s.get('session_count',0)}
                
                Tests: {s.get('test_count',0)}
                """)

    else:
        st.markdown(
            "<div class='panel'><div class='pb'><div class='empty'>"
            "<div class='empty-ico'>📚</div>"
            "Add subjects in Setup to get started."
            "</div></div></div>",
            unsafe_allow_html=True
        )

    # ── ADD SUBJECT FORM (UNCHANGED) ─────────────────────
    st.markdown(section_header("Add New Subject", "MANAGE"), unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns([3,1,1,1])

    ns_name   = c1.text_input("Subject Name", placeholder="e.g. Machine Learning", key="subj_name_inp")
    ns_icon   = c2.text_input("Icon", "📚", key="subj_icon_inp")
    ns_target = c3.number_input("Target %", 50, 100, 80, key="subj_tgt_inp")
    ns_avg    = c4.number_input("Current Avg %", 0, 100, 60, key="subj_avg_inp")

    if st.button("+ Add Subject", key="add_subj_btn"):
        if ns_name:
            new_s = {
                "name": ns_name,
                "icon": ns_icon or "📚",
                "target_score": int(ns_target),
                "avg_score": float(ns_avg),
                "color": COLS[len(subjects) % len(COLS)],
                "session_count": 0,
                "test_count": 0,
                "topics": "—"
            }

            st.session_state.subjects.append(new_s)

            try:
                db_module.save_subject(new_s)
            except:
                pass

            st.success(f"✓ {ns_name} added!")
            st.rerun()
        else:
            st.warning("Enter a subject name.")

    # ── DELETE SUBJECT (UNCHANGED) ───────────────────────
    if subjects:
        st.markdown("<br>", unsafe_allow_html=True)

        for i, s in enumerate(subjects):
            c = s.get("color", COLS[i % len(COLS)])

            col1, col2 = st.columns([5,1])

            col1.markdown(
                f"<span style='color:{c};font-size:13px;'>"
                f"{s.get('icon','📚')} {s['name']} — Avg: {round(s.get('avg_score',0))}% | "
                f"Target: {s.get('target_score',80)}%</span>",
                unsafe_allow_html=True
            )

            if col2.button("✕", key=f"del_{i}"):
                try:
                    db_module.delete_subject(subjects[i]["name"])
                except:
                    pass

                st.session_state.subjects.pop(i)
                st.rerun()