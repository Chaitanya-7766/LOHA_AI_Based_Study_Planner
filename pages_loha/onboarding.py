import streamlit as st
from datetime import date, timedelta
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pages_loha.ui_helpers import COLS
import db

STEPS = [
    {"id": "welcome",   "icon": "👋", "title": "Welcome to LOHA"},
    {"id": "profile",   "icon": "👤", "title": "Your Study Profile"},
    {"id": "subjects",  "icon": "📚", "title": "Add Your Subjects"},
    {"id": "schedule",  "icon": "📅", "title": "Generate Schedule"},
    {"id": "workflow",  "icon": "🗺️", "title": "How LOHA Works"},
]

def should_show():
    """
    Show onboarding if:
    - User is logged in
    - Has NOT completed onboarding (not stored in Supabase profile)
    - Has NOT skipped it this session
    """
    if not st.session_state.get("user"):
        return False
    if st.session_state.get("onboarding_done"):
        return False
    if st.session_state.get("onboarding_skipped"):
        return False
    # If user has subjects already, they've been through setup — skip onboarding
    if st.session_state.get("subjects"):
        st.session_state.onboarding_done = True
        return False
    return True

def show():
    step = st.session_state.get("onboarding_step", 0)

    # Full-screen overlay styles
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stSidebarCollapsedControl"] { display: none !important; }
    .block-container { padding: 0 !important; max-width: 100% !important; }

    .ob-wrap {
        min-height: 100vh;
        background: var(--bg);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        padding: 0 20px 60px;
    }

    .ob-hero {
        min-height: 42vh;
        width: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 48px 20px 34px;
    }
    .ob-hero-kicker {
        font-family: 'DM Mono', monospace;
        font-size: 10px;
        color: var(--acc);
        letter-spacing: 3px;
        text-transform: uppercase;
        margin-bottom: 12px;
    }
    .ob-hero-title {
        font-family: 'Syne', sans-serif;
        font-size: 46px;
        line-height: 1.05;
        font-weight: 800;
        color: var(--txt);
        margin-bottom: 12px;
    }
    .ob-hero-title span {
        background: linear-gradient(135deg, var(--acc), var(--acc2));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .ob-hero-sub {
        font-size: 13px;
        color: var(--muted);
        line-height: 1.7;
        max-width: 560px;
        margin-bottom: 26px;
    }
    .ob-scroll {
        display: inline-flex;
        flex-direction: column;
        align-items: center;
        gap: 9px;
        color: var(--muted);
        font-size: 10px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        animation: ob-float 1.8s ease-in-out infinite;
    }
    .ob-scroll-pill {
        width: 24px;
        height: 38px;
        border: 1px solid rgba(0,212,255,0.35);
        border-radius: 18px;
        position: relative;
    }
    .ob-scroll-pill::after {
        content: '';
        position: absolute;
        top: 8px;
        left: 50%;
        width: 4px;
        height: 7px;
        border-radius: 99px;
        background: var(--acc);
        transform: translateX(-50%);
        animation: ob-wheel 1.8s ease-in-out infinite;
    }
    @keyframes ob-float {
        0%, 100% { transform: translateY(0); opacity: .72; }
        50% { transform: translateY(8px); opacity: 1; }
    }
    @keyframes ob-wheel {
        0% { transform: translate(-50%, 0); opacity: 0; }
        35% { opacity: 1; }
        100% { transform: translate(-50%, 14px); opacity: 0; }
    }

    /* Progress steps */
    .ob-steps {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0;
        width: 100%;
        margin: 0 auto 40px;
        flex-wrap: nowrap;
    }
    .ob-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        position: relative;
    }
    .ob-step-dot {
        width: 36px; height: 36px;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 14px;
        border: 2px solid var(--brd);
        background: var(--sur2);
        color: var(--muted);
        font-weight: 700;
        transition: all 0.3s;
        z-index: 1;
    }
    .ob-step-dot.active {
        border-color: var(--acc); background: var(--acc);
        color: var(--bg); box-shadow: 0 0 14px rgba(0,212,255,0.4);
    }
    .ob-step-dot.done {
        border-color: var(--acc4); background: var(--acc4); color: #fff;
    }
    .ob-step-label {
        font-size: 9px; color: var(--muted);
        text-transform: uppercase; letter-spacing: 1px;
        text-align: center; max-width: 70px;
    }
    .ob-step-label.active { color: var(--acc); }
    .ob-step-label.done   { color: var(--acc4); }
    .ob-connector {
        width: 48px; height: 2px;
        background: var(--brd);
        margin-bottom: 22px;
        flex-shrink: 0;
    }
    .ob-connector.done { background: var(--acc4); }

    /* Card */
    .ob-card {
        background: var(--sur);
        border: 1px solid var(--brd);
        border-radius: 20px;
        padding: 40px 44px;
        width: 100%;
        max-width: 620px;
    }
    .ob-title {
        font-family: 'Syne', sans-serif;
        font-size: 22px; font-weight: 800;
        color: var(--txt); margin-bottom: 6px;
    }
    .ob-sub {
        font-size: 13px; color: var(--muted);
        margin-bottom: 24px; line-height: 1.6;
    }
    .ob-nav {
        display: flex; justify-content: space-between;
        align-items: center; margin-top: 28px;
        padding-top: 20px; border-top: 1px solid var(--brd);
    }

    /* Workflow cards */
    .wf-card {
        background: var(--sur2);
        border: 1px solid var(--brd);
        border-radius: 13px;
        padding: 16px;
        margin-bottom: 10px;
        display: flex;
        align-items: flex-start;
        gap: 14px;
        transition: border-color 0.2s;
    }
    .wf-card:hover { border-color: rgba(0,212,255,0.3); }
    .wf-num {
        width: 32px; height: 32px;
        border-radius: 50%;
        background: linear-gradient(135deg, var(--acc2), var(--acc));
        display: flex; align-items: center; justify-content: center;
        font-family: 'Syne', sans-serif; font-size: 13px; font-weight: 800;
        color: #fff; flex-shrink: 0;
    }
    .wf-title { font-family:'Syne',sans-serif; font-size:13px; font-weight:700; color:var(--txt); margin-bottom:3px; }
    .wf-desc  { font-size:12px; color:var(--muted); line-height:1.5; }
    .wf-tag   { font-size:9px; padding:2px 8px; border-radius:20px; background:rgba(0,212,255,0.1);
                color:var(--acc); border:1px solid rgba(0,212,255,0.2); font-family:'DM Mono',monospace;
                display:inline-block; margin-top:5px; }

    /* Tips */
    .tip-box {
        background: rgba(0,212,255,0.05);
        border: 1px solid rgba(0,212,255,0.15);
        border-radius: 10px;
        padding: 12px 14px;
        font-size: 12px;
        color: var(--muted);
        margin-top: 16px;
        line-height: 1.6;
    }
    .tip-box b { color: var(--acc); }

    @media (max-width: 720px) {
        .ob-hero { min-height: 38vh; padding: 38px 12px 28px; }
        .ob-hero-title { font-size: 34px; }
        .ob-card { padding: 28px 22px; }
        .ob-steps { transform: scale(.86); transform-origin: top center; }
    }
    </style>
    """, unsafe_allow_html=True)

    uname = st.session_state.get("user_name", "there")

    # ── Progress bar ──────────────────────────────────────────────────
    steps_html = ""
    for i, s in enumerate(STEPS):
        if i > 0:
            done_conn = "done" if i <= step else ""
            steps_html += f'<div class="ob-connector {done_conn}"></div>'
        dot_cls   = "active" if i == step else ("done" if i < step else "")
        label_cls = dot_cls
        dot_inner = "✓" if i < step else s["icon"]
        steps_html += f"""
        <div class="ob-step">
            <div class="ob-step-dot {dot_cls}">{dot_inner}</div>
            <div class="ob-step-label {label_cls}">{s['title']}</div>
        </div>"""

    st.markdown(f"""
    <div class="ob-hero">
        <div class="ob-hero-kicker">New account setup</div>
        <div class="ob-hero-title">Welcome to <span>LOHA</span></div>
        <div class="ob-hero-sub">
            Your AI study planner is ready. Scroll down for the quick tutorial and set up your first study plan.
        </div>
        <div class="ob-scroll">
            <div class="ob-scroll-pill"></div>
            <div>Please scroll down</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f'<div class="ob-steps">{steps_html}</div>', unsafe_allow_html=True)

    # ── Step content ──────────────────────────────────────────────────
    _, content_col, _ = st.columns([1, 12, 1])
    with content_col:
        if step == 0:
            _step_welcome(uname)
        elif step == 1:
            _step_profile()
        elif step == 2:
            _step_subjects()
        elif step == 3:
            _step_schedule()
        elif step == 4:
            _step_workflow(uname)

    # Skip button
    if step < 4:
        st.markdown("<br>", unsafe_allow_html=True)
        _, sc, _ = st.columns([2, 1, 2])
        if sc.button("Skip setup →", key="ob_skip", use_container_width=True, type="secondary"):
            st.session_state.onboarding_skipped = True
            st.rerun()


# ── Step 0: Welcome ───────────────────────────────────────────────────
def _step_welcome(uname):
    st.markdown(f"""
    <div class="ob-title">👋 Welcome, {uname}!</div>
    <div class="ob-sub">
        LOHA is your AI-powered study planner. It uses <b style="color:var(--acc);">Machine Learning</b>
        to build personalized schedules, detect weak topics, predict your exam score, and tell you
        exactly how much time you need per subject to hit your target.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:8px;">
        <div class="wf-card">
            <div style="font-size:24px;">🎯</div>
            <div><div class="wf-title">Personalized Schedule</div>
            <div class="wf-desc">AI generates your daily study plan based on exam date, difficulty, and your weak areas.</div></div>
        </div>
        <div class="wf-card">
            <div style="font-size:24px;">🧠</div>
            <div><div class="wf-title">5 ML Models</div>
            <div class="wf-desc">GradientBoost predicts scores. RandomForest detects weak topics. KMeans finds your best study time.</div></div>
        </div>
        <div class="wf-card">
            <div style="font-size:24px;">⏱️</div>
            <div><div class="wf-title">Time vs Target</div>
            <div class="wf-desc">Tracks how much time you spend per subject and tells you if it's enough to reach your target score.</div></div>
        </div>
        <div class="wf-card">
            <div style="font-size:24px;">🔁</div>
            <div><div class="wf-title">Spaced Repetition</div>
            <div class="wf-desc">SM-2 algorithm schedules your review sessions at the perfect interval so you never forget.</div></div>
        </div>
    </div>
    <div class="tip-box">
        💡 <b>Quick setup takes 2 minutes.</b> We'll collect your subjects, exam date, and daily hours —
        then LOHA's AI will handle everything else automatically.
    </div>
    """, unsafe_allow_html=True)

    _, btn_col = st.columns([3, 1])
    if btn_col.button("Let's start →", key="ob_next_0", use_container_width=True):
        st.session_state.onboarding_step = 1
        st.rerun()


# ── Step 1: Profile ───────────────────────────────────────────────────
def _step_profile():
    st.markdown("""
    <div class="ob-title">👤 Your Study Profile</div>
    <div class="ob-sub">Tell LOHA about your exam and study habits. This helps the AI build the right schedule for you.</div>
    """, unsafe_allow_html=True)

    prof = st.session_state.get("profile", {})

    with st.form("ob_profile_form"):
        c1, c2 = st.columns(2)
        p_name   = c1.text_input("Full Name", prof.get("full_name", st.session_state.get("user_name","")),
                                   placeholder="e.g. Chaitanya Kumar")
        p_exam   = c2.date_input("📅 Exam Date",
                                   value=date.today() + timedelta(days=30),
                                   min_value=date.today() + timedelta(days=1))

        c3, c4 = st.columns(2)
        p_hours  = c3.slider("⏰ Daily Study Hours", 1.0, 12.0, float(prof.get("daily_hours", 4)), 0.5)
        p_target = c4.number_input("🎯 Default Target Score %", 50, 100, int(prof.get("target_score", 80)))

        c5, c6 = st.columns(2)
        peak_opts = ["morning","afternoon","evening","night"]
        peak_lbls = ["Morning (6–10 AM)","Afternoon (12–4 PM)","Evening (8–11 PM)","Late Night (11 PM–2 AM)"]
        cur_peak  = prof.get("peak_time","evening")
        p_peak    = c5.selectbox("🕐 Best Study Time", peak_lbls,
                                  index=peak_opts.index(cur_peak) if cur_peak in peak_opts else 2)
        style_opts = ["Visual (diagrams)","Practice problems","Read then revise","Flashcards"]
        p_style    = c6.selectbox("📖 Learning Style", style_opts, index=1)

        saved = st.form_submit_button("Save & Continue →", use_container_width=True)
        if saved:
            st.session_state.profile = {
                "full_name": p_name, "daily_hours": p_hours,
                "target_score": p_target,
                "exam_date": str(p_exam),
                "peak_time": peak_opts[peak_lbls.index(p_peak)],
                "learning_style": p_style,
            }
            try:
                sb = db.get_supabase()
                uid = st.session_state.get("user_id")
                if sb and uid:
                    sb.table("profiles").upsert({
                        "id": uid, "full_name": p_name,
                        "daily_hours": p_hours, "target_score": p_target,
                        "exam_date": str(p_exam),
                        "peak_time": peak_opts[peak_lbls.index(p_peak)],
                        "learning_style": p_style,
                    }, on_conflict="id").execute()
            except: pass
            st.session_state.onboarding_step = 2
            st.rerun()

    st.markdown("""
    <div class="tip-box">
        💡 <b>Tip:</b> Your exam date is used to calculate how much time you have left and how
        intensively LOHA should schedule your study sessions. You can always update this in <b>Setup</b>.
    </div>
    """, unsafe_allow_html=True)

    back_col, _ = st.columns([1, 3])
    if back_col.button("← Back", key="ob_back_1", type="secondary"):
        st.session_state.onboarding_step = 0
        st.rerun()


# ── Step 2: Subjects ──────────────────────────────────────────────────
def _step_subjects():
    st.markdown("""
    <div class="ob-title">📚 Add Your Subjects</div>
    <div class="ob-sub">Add all subjects you're studying. Set a target score for each — LOHA will prioritize
    weaker subjects automatically in your schedule.</div>
    """, unsafe_allow_html=True)

    if "subjects" not in st.session_state:
        st.session_state.subjects = []
    subjects = st.session_state.subjects

    # Add subject form
    with st.form("ob_add_subj"):
        ac1, ac2, ac3, ac4 = st.columns([3, 1, 1, 1])
        s_name   = ac1.text_input("Subject Name", placeholder="e.g. Machine Learning")
        s_icon   = ac2.text_input("Icon", "📚")
        s_target = ac3.number_input("Target %", 50, 100, int(st.session_state.get("profile",{}).get("target_score",80)))
        s_avg    = ac4.number_input("Current %", 0, 100, 50)
        if st.form_submit_button("+ Add Subject", use_container_width=True):
            if s_name:
                st.session_state.subjects.append({
                    "name": s_name, "icon": s_icon or "📚",
                    "target_score": int(s_target), "avg_score": float(s_avg),
                    "color": COLS[len(subjects) % len(COLS)],
                    "session_count": 0, "test_count": 0, "topics": "—",
                })
                st.success(f"✅ {s_name} added!")
                st.rerun()
            else:
                st.warning("Enter a subject name.")

    # Show added subjects
    if subjects:
        st.markdown("<br>", unsafe_allow_html=True)
        for i, s in enumerate(subjects):
            c   = s.get("color", COLS[i % len(COLS)])
            gap = s.get("target_score",80) - s.get("avg_score",50)
            priority = "🔴 High" if gap > 20 else ("🟡 Medium" if gap > 10 else "🟢 Low")
            col1, col2, col3 = st.columns([4, 2, 1])
            col1.markdown(f"""
            <div style="display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid var(--brd);">
                <span style="font-size:18px;">{s.get('icon','📚')}</span>
                <div>
                    <span style="color:{c};font-weight:600;font-size:13px;">{s['name']}</span>
                    <span style="color:var(--muted);font-size:11px;margin-left:8px;">
                        Current: {round(s.get('avg_score',0))}% → Target: {s.get('target_score',80)}%
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            col2.markdown(f"<div style='padding:10px 0;font-size:11px;'>{priority} priority</div>", unsafe_allow_html=True)
            if col3.button("✕", key=f"ob_del_{i}"):
                st.session_state.subjects.pop(i)
                st.rerun()
    else:
        st.markdown("""
        <div class="tip-box" style="text-align:center;">
            📚 Add at least 2-3 subjects to get the most out of LOHA's AI scheduling.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="tip-box">
        💡 <b>Tip:</b> Be honest about your current score — LOHA uses this to detect weak areas
        and allocate more study time where you need it most. Higher priority = more schedule slots.
    </div>
    """, unsafe_allow_html=True)

    bc, _, nc = st.columns([1, 2, 1])
    if bc.button("← Back", key="ob_back_2", type="secondary"):
        st.session_state.onboarding_step = 1; st.rerun()
    if nc.button("Continue →", key="ob_next_2", use_container_width=True):
        if not subjects:
            st.warning("⚠️ Add at least one subject to continue.")
        else:
            st.session_state.onboarding_step = 3; st.rerun()


# ── Step 3: Schedule Preview ──────────────────────────────────────────
def _step_schedule():
    st.markdown("""
    <div class="ob-title">📅 Generate Your First Schedule</div>
    <div class="ob-sub">LOHA will now generate a personalized AI study schedule based on your profile
    and subjects. You can regenerate it anytime from the Schedule page.</div>
    """, unsafe_allow_html=True)

    profile  = st.session_state.get("profile", {})
    subjects = st.session_state.get("subjects", [])

    # Preview summary
    exam_date = profile.get("exam_date","")
    try:
        ed   = date.fromisoformat(exam_date[:10])
        days = max(0, (ed - date.today()).days)
    except:
        days = 30

    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px;">
        <div style="background:var(--sur2);border:1px solid var(--brd);border-radius:12px;padding:14px;text-align:center;">
            <div style="font-family:'DM Mono',monospace;font-size:24px;color:var(--acc);font-weight:600;">{days}</div>
            <div style="font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;">Days to Exam</div>
        </div>
        <div style="background:var(--sur2);border:1px solid var(--brd);border-radius:12px;padding:14px;text-align:center;">
            <div style="font-family:'DM Mono',monospace;font-size:24px;color:var(--acc2);font-weight:600;">{len(subjects)}</div>
            <div style="font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;">Subjects</div>
        </div>
        <div style="background:var(--sur2);border:1px solid var(--brd);border-radius:12px;padding:14px;text-align:center;">
            <div style="font-family:'DM Mono',monospace;font-size:24px;color:var(--acc3);font-weight:600;">{profile.get('daily_hours',4)}h</div>
            <div style="font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;">Daily Hours</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Subject priority preview
    st.markdown("<div style='font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;'>AI Priority Order (highest gap first)</div>", unsafe_allow_html=True)
    sorted_subjs = sorted(subjects, key=lambda s: s.get("target_score",80)-s.get("avg_score",50), reverse=True)
    for i, s in enumerate(sorted_subjs):
        c   = s.get("color", COLS[i % len(COLS)])
        gap = s.get("target_score",80) - s.get("avg_score",50)
        pct = min(100, round(s.get("avg_score",0) / s.get("target_score",80) * 100)) if s.get("target_score",80) > 0 else 0
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
            <span style="font-size:16px;">{s.get('icon','📚')}</span>
            <div style="flex:1;">
                <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
                    <span style="color:{c};font-size:12px;font-weight:600;">{s['name']}</span>
                    <span style="font-size:11px;color:var(--muted);">Gap: {gap:.0f}pts</span>
                </div>
                <div style="height:4px;background:var(--sur2);border-radius:100px;overflow:hidden;">
                    <div style="width:{pct}%;height:100%;background:{c};border-radius:100px;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="tip-box">
        💡 <b>How scheduling works:</b> LOHA allocates more daily time to subjects where you have the
        biggest gap to your target score. Subjects with <b style="color:#ef4444;">critical</b> or
        <b style="color:#f59e0b;">weak</b> status get priority morning/evening slots.
    </div>
    """, unsafe_allow_html=True)

    bc, _, nc = st.columns([1, 2, 1])
    if bc.button("← Back", key="ob_back_3", type="secondary"):
        st.session_state.onboarding_step = 2; st.rerun()
    if nc.button("Generate & Continue →", key="ob_next_3", use_container_width=True):
        # Auto-generate first week schedule
        try:
            from ml_engine import generate_schedule
            from datetime import timedelta
            start = date.today()
            end   = start + timedelta(days=6)
            enriched = [{**s, "subject_id": s["name"],
                "weakness_score": max(0, int((s.get("target_score",80)-s.get("avg_score",60))/20))}
                for s in subjects]
            slots = generate_schedule(
                subjects=enriched, start_date=start, end_date=end,
                daily_hours=float(profile.get("daily_hours",4)),
                peak_time=profile.get("peak_time","evening"),
            )
            subj_map = {s["name"]:s for s in subjects}
            for slot in slots:
                sname = slot.get("subject_name","")
                info  = subj_map.get(sname,{})
                slot["subjects"] = {"name":sname,"icon":info.get("icon","📚"),"color":info.get("color",COLS[0])}
            st.session_state.schedule_slots = slots
            st.success(f"✨ Generated {len(slots)} schedule slots!")
        except Exception as e:
            st.warning(f"Schedule will be generated on the Schedule page. ({e})")
        st.session_state.onboarding_step = 4
        st.rerun()


# ── Step 4: How LOHA Works (full workflow) ────────────────────────────
def _step_workflow(uname):
    st.markdown(f"""
    <div class="ob-title">🗺️ You're all set, {uname.split()[0]}!</div>
    <div class="ob-sub">Here's exactly how to use LOHA for maximum results. Follow this workflow daily.</div>
    """, unsafe_allow_html=True)

    workflow = [
        {
            "icon": "⚙️", "page": "Setup",
            "tag": "ONE TIME",
            "title": "Configure Profile & Subjects",
            "desc": "Add all your subjects with current score and target score. Set your exam date and daily study hours. LOHA uses this as the foundation for all AI decisions.",
            "tips": ["Be honest about your current score — the AI needs accurate data", "Set realistic targets (don't put 100% if you're at 40%)", "Update your score as you improve"]
        },
        {
            "icon": "📅", "page": "Schedule",
            "tag": "WEEKLY",
            "title": "Generate AI Study Schedule",
            "desc": "LOHA creates a personalized weekly schedule prioritizing weak subjects. Regenerate every week as your performance changes.",
            "tips": ["Click '✨ Generate Schedule' every Monday", "Mark slots as Done after completing them", "The AI auto-boosts time for subjects you're struggling with"]
        },
        {
            "icon": "⏱️", "page": "Focus Timer",
            "tag": "DAILY",
            "title": "Study with Pomodoro Timer",
            "desc": "Use the built-in 25/50-min timer for each study session. Log your session with duration and self-score — this feeds the ML models.",
            "tips": ["Always log duration — it powers the Time vs Target analysis", "Rate yourself honestly (self-score) after each session", "Do at least 2 Pomodoros per subject per day"]
        },
        {
            "icon": "🧠", "page": "AI Insights",
            "tag": "WEEKLY",
            "title": "Check ML Analysis",
            "desc": "Run the 5 ML models to get: weak topic detection, exam score prediction, optimal study times, spaced repetition schedule, and time vs target analysis.",
            "tips": ["Run 'Weak Topic Detector' weekly to see which subjects need attention", "Check 'Time Spent vs Target' to know if you're studying enough", "Use 'Exam Score Predictions' to stay motivated"]
        },
        {
            "icon": "📈", "page": "Analytics",
            "tag": "WEEKLY",
            "title": "Review Your Progress",
            "desc": "The heatmap shows your consistency. Score trend shows if you're improving. Add test scores after every test to keep predictions accurate.",
            "tips": ["Log test scores immediately after exams", "A green heatmap = consistent study = better results", "If trend is declining, check AI Insights for recommendations"]
        },
        {
            "icon": "📄", "page": "Syllabus Parser (via chatbot)",
            "tag": "AS NEEDED",
            "title": "Parse Your Syllabus",
            "desc": "Paste your syllabus text to extract topics, get difficulty ratings, and identify which topics to prioritize. Use the chatbot for study guidance anytime.",
            "tips": ["Parse syllabus at the start of each semester", "High-difficulty topics = schedule more time for them", "Ask the chatbot for study tips on specific topics"]
        },
    ]

    for i, w in enumerate(workflow):
        tips_html = "".join([f'<li style="color:var(--muted);margin-bottom:3px;">{t}</li>' for t in w["tips"]])
        st.markdown(f"""
        <div class="wf-card">
            <div class="wf-num">{i+1}</div>
            <div style="flex:1;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                    <span style="font-size:18px;">{w['icon']}</span>
                    <span class="wf-title">{w['title']}</span>
                    <span class="wf-tag">{w['tag']}</span>
                    <span style="font-size:10px;color:var(--acc2);margin-left:auto;">→ {w['page']}</span>
                </div>
                <div class="wf-desc">{w['desc']}</div>
                <ul style="margin:8px 0 0 16px;font-size:11px;list-style:disc;">
                    {tips_html}
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="tip-box">
        🏆 <b>Best practice:</b> Log every study session in Focus Timer →
        Check AI Insights weekly → Regenerate schedule as your scores improve.
        The more data LOHA has, the smarter its predictions become!
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    _, btn_col, _ = st.columns([1, 2, 1])
    if btn_col.button("🚀 Start Using LOHA!", key="ob_finish", use_container_width=True):
        st.session_state.onboarding_done = True
        # Persist onboarding completion
        try:
            sb  = db.get_supabase()
            uid = st.session_state.get("user_id")
            if sb and uid:
                sb.table("profiles").upsert(
                    {"id": uid, "onboarding_done": True}, on_conflict="id"
                ).execute()
        except:
            pass
        st.rerun()
