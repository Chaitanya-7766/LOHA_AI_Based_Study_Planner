import streamlit as st
from datetime import datetime

def show():
    st.markdown("""
    <div style='text-align:center; padding: 3rem 0 2rem;'>
        <div style='font-family:Syne; font-size:3.5rem; font-weight:800;
                    background: linear-gradient(135deg, #a78bfa, #60a5fa, #34d399);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                    line-height:1.1;'>
            LOHA
        </div>
        <div style='color:#94a3b8; font-size:1.1rem; margin-top:0.5rem; letter-spacing:3px;'>
            AI-BASED STUDY PLAN GENERATOR
        </div>
        <div style='color:#475569; font-size:0.85rem; margin-top:0.5rem;'>
            CVR College of Engineering · BTech III Year CSE(AI&ML)-A
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Feature cards
    cols = st.columns(3)
    features = [
        ("📅", "Smart Scheduling", "Generates personalized daily & weekly study plans based on your deadlines and capacity."),
        ("🧠", "AI Difficulty Scoring", "NLP-powered topic difficulty estimation to prioritize your weak areas first."),
        ("📊", "Progress Prediction", "ML-based trend analysis tracks your learning curve and predicts future performance."),
        ("💬", "AI Chatbot", "Ask study questions, get tips, and receive guidance 24/7 powered by NLP."),
        ("🔥", "Streak System", "Gamified daily streaks keep you motivated and consistent in your studies."),
        ("⏱️", "Pomodoro Timer", "Built-in focus timer to maximize productivity during study sessions."),
    ]

    for i, (icon, title, desc) in enumerate(features):
        with cols[i % 3]:
            st.markdown(f"""
            <div class='card' style='min-height:140px;'>
                <div style='font-size:2rem;'>{icon}</div>
                <div style='font-family:Syne; font-weight:700; color:#e2e8f0; font-size:1rem; margin:0.5rem 0;'>{title}</div>
                <div style='color:#64748b; font-size:0.85rem; line-height:1.5;'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Quick start
    st.markdown("""
    <div style='font-family:Syne; font-size:1.4rem; font-weight:700; color:#e2e8f0; margin-bottom:1rem;'>
        🚀 Quick Start
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class='card'>
            <div style='font-family:Syne; color:#a78bfa; font-size:1rem; font-weight:700; margin-bottom:0.8rem;'>
                How LOHA works
            </div>
            <div style='color:#94a3b8; font-size:0.9rem; line-height:2;'>
                1️⃣ Enter your subjects & exam dates<br>
                2️⃣ Set daily available study hours<br>
                3️⃣ Optionally paste your syllabus<br>
                4️⃣ Get a personalized AI schedule<br>
                5️⃣ Track progress & adjust dynamically
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class='card'>
            <div style='font-family:Syne; color:#34d399; font-size:1rem; font-weight:700; margin-bottom:0.8rem;'>
                Tech Stack
            </div>
            <div style='color:#94a3b8; font-size:0.9rem; line-height:2;'>
                🖥️ <b style='color:#e2e8f0;'>Streamlit</b> — Interactive UI<br>
                🤖 <b style='color:#e2e8f0;'>Scikit-learn</b> — ML Scheduling<br>
                📝 <b style='color:#e2e8f0;'>NLTK / Regex NLP</b> — Syllabus Parsing<br>
                🗄️ <b style='color:#e2e8f0;'>Supabase</b> — Cloud Database<br>
                📊 <b style='color:#e2e8f0;'>Plotly</b> — Visualizations
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Pomodoro Timer
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-family:Syne; font-size:1.4rem; font-weight:700; color:#e2e8f0; margin-bottom:1rem;'>
        ⏱️ Pomodoro Focus Timer
    </div>
    """, unsafe_allow_html=True)

    timer_col, _, _ = st.columns([2,1,1])
    with timer_col:
        st.markdown("""
        <div class='card' style='text-align:center;'>
            <div style='color:#94a3b8; font-size:0.85rem; margin-bottom:1rem;'>
                Standard Pomodoro: 25 min focus → 5 min break
            </div>
            <div id='timer' style='font-family:Syne; font-size:3rem; font-weight:800; 
                                    color:#a78bfa; letter-spacing:4px;'>
                25:00
            </div>
            <div style='color:#475569; font-size:0.8rem; margin-top:0.5rem;' id='timer-label'>
                Focus Session
            </div>
        </div>
        <script>
        let seconds = 25*60;
        let running = false;
        let interval;
        let phase = 'focus';
        function fmt(s) {
            let m = Math.floor(s/60).toString().padStart(2,'0');
            let sec = (s%60).toString().padStart(2,'0');
            return m+':'+sec;
        }
        </script>
        """, unsafe_allow_html=True)

        col_a, col_b, col_c = st.columns(3)
        if col_a.button("▶ Start", key="pom_start"):
            st.session_state["pom_running"] = True
        if col_b.button("⏸ Pause", key="pom_pause"):
            st.session_state["pom_running"] = False
        if col_c.button("↺ Reset", key="pom_reset"):
            st.session_state["pom_mins"] = 25

        pom_mins = st.slider("Focus duration (minutes)", 5, 60, 25, key="pom_mins_slider")
        st.info(f"⏱️ Timer set to **{pom_mins} minutes**. Use a browser Pomodoro extension for live countdown.")

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center; color:#1e293b; font-size:0.8rem;'>
        Built with ❤️ by K. Sai Chaitanya Varma · G. Shiva Kumar · N. Tarun Kumar
    </div>
    """, unsafe_allow_html=True)