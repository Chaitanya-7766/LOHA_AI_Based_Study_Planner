import streamlit as st
from datetime import date
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pages_loha.ui_helpers import page_header, section_header, COLS
import db

def show():
    st.title("Focus Timer")
    st.caption("Pomodoro-powered deep work sessions")
    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)

    subjects   = st.session_state.get("subjects", [])
    logs       = st.session_state.get("progress_log", [])
    profile    = st.session_state.get("profile", {})
    today      = date.today().strftime("%Y-%m-%d")
    today_logs = [l for l in logs if l.get("date") == today]

    subj_options = [f"{s.get('icon','📚')} {s['name']}" for s in subjects] if subjects else ["📚 General Study"]

    # ── Subject & Target Setup ────────────────────────────────────────
    st.markdown(section_header("Subject & Target", "SESSION SETUP"), unsafe_allow_html=True)

    c1, c2, c3 = st.columns([3, 2, 2])
    chosen_label = c1.selectbox("Subject", subj_options, key="focus_subj_sel",
                                 label_visibility="collapsed")
    chosen_name  = chosen_label.split(" ", 1)[-1] if " " in chosen_label else chosen_label

    subj_data      = next((s for s in subjects if s["name"] == chosen_name), {})
    default_target = int(subj_data.get("target_score", 80))
    default_hours  = float(profile.get("daily_hours", 4))

    c2.markdown('<div style="font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:4px;">TARGET SCORE %</div>', unsafe_allow_html=True)
    target_score   = c2.number_input("Target Score %", 0, 100, default_target,
                                      key="focus_target", label_visibility="collapsed")

    c3.markdown('<div style="font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:4px;">DAILY GOAL (HRS)</div>', unsafe_allow_html=True)
    daily_goal_hrs = c3.number_input("Daily Goal (hrs)", 0.5, 8.0, default_hours,
                                      step=0.5, key="focus_daily_goal",
                                      label_visibility="collapsed")

    # Progress bar for today's study on this subject
    time_today     = sum(l.get("duration_mins", 25) for l in today_logs if l.get("subject") == chosen_name)
    time_today_hrs = round(time_today / 60, 2)
    goal_mins      = daily_goal_hrs * 60
    pct_done       = min(100, round(time_today / goal_mins * 100)) if goal_mins > 0 else 0
    bar_color      = "#10b981" if pct_done >= 100 else ("#f59e0b" if pct_done >= 50 else "#00d4ff")

    goal_html  = '<div style="font-size:11px;color:#10b981;margin-top:5px;">✅ Daily goal reached!</div>' if pct_done >= 100 else ""
    st.markdown(f"""
    <div style="margin-top:10px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
            <span style="font-size:11px;color:var(--muted);">
                Today on <b style="color:var(--txt);">{chosen_name}</b>:
                <b style="color:{bar_color};">{time_today_hrs}h</b>
                of <b style="color:var(--txt);">{daily_goal_hrs}h</b> goal
            </span>
            <span style="font-family:'DM Mono',monospace;font-size:11px;color:{bar_color};">{pct_done}%</span>
        </div>
        <div style="height:5px;background:var(--sur2);border-radius:100px;overflow:hidden;">
            <div style="width:{pct_done}%;height:100%;background:{bar_color};border-radius:100px;transition:width 0.5s;"></div>
        </div>
        {goal_html}
    </div>
    """, unsafe_allow_html=True)

    # ── Pomodoro Timer (JavaScript) ───────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(section_header("Pomodoro Focus Timer", "AI TRACKED"), unsafe_allow_html=True)

    # Subject selector label
    if subjects:
        st.markdown('<div style="font-size:11px;color:var(--muted);margin-bottom:8px;">Selected: '
                    f'<b style="color:var(--acc);">{chosen_name}</b></div>', unsafe_allow_html=True)

    # Today's chips
    chips_html = ""
    if today_logs:
        for l in today_logs:
            c_col = COLS[hash(str(l.get("subject", ""))) % len(COLS)]
            dur   = l.get("duration_mins", 25)
            chips_html += (f'<span style="display:inline-flex;align-items:center;gap:5px;'
                          f'background:#121a2b;border:1px solid {c_col}44;border-radius:20px;'
                          f'padding:5px 10px;font-size:11px;color:{c_col};margin:2px;">'
                          f'📚 {l.get("subject","")} · {dur}min · {l.get("score",0)}%</span>')
    else:
        chips_html = '<span style="font-size:12px;color:#5a7090;">No sessions yet today.</span>'

    st.components.v1.html(f"""
    <!DOCTYPE html><html><head>
    <style>
    *{{margin:0;padding:0;box-sizing:border-box;}}
    body{{background:transparent;font-family:'DM Sans',sans-serif;color:#e2eaf8;}}
    .mode-tabs{{display:flex;gap:4px;background:#121a2b;border-radius:10px;padding:4px;margin-bottom:16px;}}
    .mode-tab{{flex:1;padding:9px;text-align:center;border-radius:8px;cursor:pointer;font-size:12px;
               font-weight:500;color:#5a7090;border:none;background:transparent;transition:all .2s;}}
    .mode-tab.active{{background:#00d4ff;color:#080c14;font-weight:700;}}
    .mode-tab:hover:not(.active){{color:#e2eaf8;background:#1e2d45;}}
    .sessions-row{{display:flex;align-items:center;justify-content:center;gap:8px;margin-bottom:12px;}}
    .session-dot{{width:10px;height:10px;border-radius:50%;background:#1e2d45;transition:all .3s;}}
    .session-dot.done{{background:#00d4ff;box-shadow:0 0 6px rgba(0,212,255,.5);}}
    .session-dot.current{{background:#f59e0b;box-shadow:0 0 6px rgba(245,158,11,.5);animation:pulse 1s infinite;}}
    .session-label{{font-size:10px;color:#5a7090;letter-spacing:1px;}}
    @keyframes pulse{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.3)}}}}
    .ring-wrap{{display:flex;justify-content:center;margin:4px 0 8px;position:relative;}}
    .ring-svg{{transform:rotate(-90deg);}}
    .ring-bg{{fill:none;stroke:#1e2d45;stroke-width:5;}}
    .ring-fg{{fill:none;stroke:#00d4ff;stroke-width:5;stroke-linecap:round;transition:stroke-dashoffset 1s linear,stroke .5s;}}
    .ring-center{{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;}}
    .timer-display{{font-family:'DM Mono','Courier New',monospace;font-size:52px;font-weight:500;
                    color:#00d4ff;letter-spacing:4px;text-shadow:0 0 40px rgba(0,212,255,.5);
                    transition:color .5s;line-height:1;}}
    .timer-display.brk{{color:#10b981;text-shadow:0 0 40px rgba(16,185,129,.5);}}
    .timer-display.warn{{color:#f59e0b;text-shadow:0 0 40px rgba(245,158,11,.5);}}
    .timer-display.danger{{color:#ef4444;text-shadow:0 0 40px rgba(239,68,68,.5);animation:flash 1s infinite;}}
    @keyframes flash{{0%,100%{{opacity:1}}50%{{opacity:.5}}}}
    .phase-lbl{{font-size:10px;color:#5a7090;letter-spacing:3px;text-transform:uppercase;margin-top:4px;}}
    .controls{{display:flex;justify-content:center;gap:10px;margin:16px 0;}}
    .btn{{padding:10px 28px;border-radius:9px;border:none;cursor:pointer;font-size:13px;font-weight:700;font-family:inherit;transition:all .15s;}}
    .btn-pri{{background:#00d4ff;color:#080c14;min-width:130px;}}
    .btn-pri:hover{{background:#00bcd4;transform:translateY(-1px);box-shadow:0 4px 20px rgba(0,212,255,.3);}}
    .btn-ghost{{background:#121a2b;color:#e2eaf8;border:1px solid #1e2d45;}}
    .btn-ghost:hover{{border-color:#00d4ff;color:#00d4ff;}}
    .elapsed{{text-align:center;font-family:'DM Mono',monospace;font-size:11px;color:#5a7090;margin-bottom:8px;}}
    .divider{{height:1px;background:#1e2d45;margin:14px 0;}}
    .today-label{{font-size:10px;color:#5a7090;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px;}}
    .notif{{position:fixed;top:16px;right:16px;background:#0d1420;border:1px solid #00d4ff;
             border-radius:10px;padding:12px 16px;font-size:13px;color:#e2eaf8;
             opacity:0;transform:translateY(-10px);transition:all .3s;pointer-events:none;z-index:999;}}
    .notif.show{{opacity:1;transform:translateY(0);}}
    </style></head><body>
    <div class="notif" id="notif">⏰ Time's up!</div>
    <div class="mode-tabs">
        <button class="mode-tab active" onclick="setMode(25,'focus',this)">25 min</button>
        <button class="mode-tab"        onclick="setMode(50,'focus',this)">50 min</button>
        <button class="mode-tab"        onclick="setMode(5,'break',this)">5 min Break</button>
        <button class="mode-tab"        onclick="setMode(15,'break',this)">15 min Break</button>
    </div>
    <div class="sessions-row">
        <span class="session-label">SESSION</span>
        <div class="session-dot current" id="d0"></div>
        <div class="session-dot" id="d1"></div>
        <div class="session-dot" id="d2"></div>
        <div class="session-dot" id="d3"></div>
        <span class="session-label">OF 4</span>
    </div>
    <div class="ring-wrap">
        <svg class="ring-svg" width="200" height="200" viewBox="0 0 200 200">
            <circle class="ring-bg" cx="100" cy="100" r="88"/>
            <circle class="ring-fg" id="ring" cx="100" cy="100" r="88"
                    stroke-dasharray="553" stroke-dashoffset="0"/>
        </svg>
        <div class="ring-center">
            <div class="timer-display" id="timer">25:00</div>
            <div class="phase-lbl" id="phase">FOCUS SESSION</div>
        </div>
    </div>
    <div class="elapsed" id="elapsed">Elapsed: 0 min 0 sec</div>
    <div class="controls">
        <button class="btn btn-ghost" onclick="resetTimer()">↺ Reset</button>
        <button class="btn btn-pri"   onclick="toggleTimer()" id="startBtn">▶ Start</button>
    </div>
    <div class="divider"></div>
    <div class="today-label">Today's completed sessions</div>
    <div id="chips">{chips_html}</div>
    <script>
    const CIRC=2*Math.PI*88;
    let total=25*60,rem=25*60,elapsed=0,running=false,iv=null,mode='focus',done=0;
    function fmt(s){{return String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0');}}
    function update(){{
        const t=document.getElementById('timer'),r=document.getElementById('ring'),pct=rem/total;
        r.style.strokeDasharray=CIRC;r.style.strokeDashoffset=CIRC*(1-pct);
        t.textContent=fmt(rem);t.className='timer-display';
        if(mode==='break'){{t.classList.add('brk');r.style.stroke='#10b981';}}
        else if(rem<=60){{t.classList.add('danger');r.style.stroke='#ef4444';}}
        else if(rem<=total*.25){{t.classList.add('warn');r.style.stroke='#f59e0b';}}
        else{{r.style.stroke='#00d4ff';}}
        const e=document.getElementById('elapsed');
        e.textContent='Elapsed: '+Math.floor(elapsed/60)+' min '+elapsed%60+' sec';
    }}
    function toggleTimer(){{
        const btn=document.getElementById('startBtn');
        if(running){{clearInterval(iv);running=false;btn.textContent='▶ Resume';}}
        else{{running=true;btn.textContent='⏸ Pause';
            iv=setInterval(()=>{{if(rem>0){{rem--;elapsed++;update();}}else{{clearInterval(iv);running=false;btn.textContent='▶ Start';onEnd();}}}},1000);}}
    }}
    function resetTimer(){{clearInterval(iv);running=false;rem=total;elapsed=0;document.getElementById('startBtn').textContent='▶ Start';update();}}
    function setMode(mins,m,el){{
        document.querySelectorAll('.mode-tab').forEach(t=>t.classList.remove('active'));el.classList.add('active');
        mode=m;total=mins*60;rem=mins*60;elapsed=0;clearInterval(iv);running=false;
        document.getElementById('startBtn').textContent='▶ Start';
        document.getElementById('phase').textContent=m==='break'?(mins===5?'SHORT BREAK':'LONG BREAK'):(mins===25?'FOCUS SESSION':'DEEP FOCUS');
        update();
    }}
    function onEnd(){{
        const n=document.getElementById('notif');
        if(mode==='focus'){{done=Math.min(done+1,4);updateDots();n.textContent='🎯 Session complete! Take a break.';
            setTimeout(()=>document.querySelectorAll('.mode-tab')[2].click(),2000);}}
        else{{n.textContent='⚡ Break over! Back to focus.';setTimeout(()=>document.querySelectorAll('.mode-tab')[0].click(),2000);}}
        n.classList.add('show');setTimeout(()=>n.classList.remove('show'),3500);beep(mode==='focus'?880:660);
    }}
    function updateDots(){{
        ['d0','d1','d2','d3'].forEach((id,i)=>{{const d=document.getElementById(id);d.className='session-dot';
            if(i<done)d.classList.add('done');else if(i===done)d.classList.add('current');}});
        if(done>=4)setTimeout(()=>{{done=0;updateDots();}},3000);
    }}
    function beep(f){{try{{var c=new AudioContext();[0,.3,.6].forEach(function(d){{var o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.frequency.value=f;g.gain.setValueAtTime(.3,c.currentTime+d);g.gain.exponentialRampToValueAtTime(.001,c.currentTime+d+.4);o.start(c.currentTime+d);o.stop(c.currentTime+d+.4);}})}}catch(e){{}}}}
    update();
    </script></body></html>
    """, height=530)

    # ── Log Session ───────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📝 Log Completed Session", expanded=True):
        with st.form("focus_log_form"):
            r1, r2, r3 = st.columns(3)
            log_subj   = r1.text_input("Subject", chosen_name)
            log_topic  = r2.text_input("Topic Studied", placeholder="e.g. Neural Networks")
            log_dur    = r3.number_input("Duration (mins)", 5, 180, 25)
            r4, r5, r6 = st.columns(3)
            log_score  = r4.slider("Self-score %", 0, 100, 75)
            log_target = r5.number_input("Target Score %", 0, 100, default_target)
            log_diff   = r6.slider("Difficulty (1-5)", 1, 5, 3)
            if st.form_submit_button("✅ Log Session", use_container_width=True):
                entry = {
                    "subject":          log_subj,
                    "topic":            log_topic,
                    "date":             today,
                    "score":            log_score,
                    "target_score":     log_target,
                    "duration_mins":    int(log_dur),
                    "difficulty":       log_diff,
                    "completed":        True,
                    "completed_topics": 1,
                }
                if "progress_log" not in st.session_state:
                    st.session_state.progress_log = []
                st.session_state.progress_log.append(entry)
                # Update subject avg_score in session
                for i, s in enumerate(st.session_state.subjects):
                    if s["name"] == log_subj:
                        count   = s.get("session_count", 0) + 1
                        old_avg = s.get("avg_score", log_score)
                        new_avg = round((old_avg * (count - 1) + log_score) / count, 1)
                        st.session_state.subjects[i]["avg_score"]     = new_avg
                        st.session_state.subjects[i]["target_score"]  = log_target
                        st.session_state.subjects[i]["session_count"] = count
                        try:
                            db.save_subject(st.session_state.subjects[i])
                        except:
                            pass
                        break
                try:
                    db.save_progress(entry)
                except:
                    pass
                st.success(f"✅ Logged {log_dur} min session for {log_subj}!")
                st.rerun()

    # ── Time Analysis per Subject (ML) ────────────────────────────────
    if logs:
        import pandas as pd, numpy as np
        df = pd.DataFrame(logs)
        df["score"]         = pd.to_numeric(df["score"],         errors="coerce").fillna(0)
        df["duration_mins"] = pd.to_numeric(df.get("duration_mins", pd.Series([25]*len(df))),
                                             errors="coerce").fillna(25) \
                              if "duration_mins" in df.columns else pd.Series([25]*len(df))
        df["target_score"]  = pd.to_numeric(df.get("target_score", pd.Series([80]*len(df))),
                                             errors="coerce").fillna(80) \
                              if "target_score" in df.columns else pd.Series([80]*len(df))

        if "subject" in df.columns and df["subject"].notna().any():
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(section_header("⏱️ Time Analysis vs Target Score", "ML INSIGHTS"),
                        unsafe_allow_html=True)

            for subj_name in df["subject"].dropna().unique():
                sdf          = df[df["subject"] == subj_name]
                total_mins   = float(sdf["duration_mins"].sum())
                total_hrs    = round(total_mins / 60, 2)
                avg_score    = round(float(sdf["score"].mean()), 1)
                target       = float(sdf["target_score"].iloc[-1]) if "target_score" in sdf.columns else 80.0
                n_sessions   = len(sdf)
                avg_diff     = float(sdf["difficulty"].mean()) if "difficulty" in sdf.columns else 3.0

                # ML: required hours
                gap               = max(0.0, target - avg_score)
                diff_factor       = avg_diff / 3.0
                efficiency        = max(0.1, avg_score / 100.0)
                required_hrs      = round(max(1.0, gap * diff_factor * 1.2 / efficiency), 1) if gap > 0 else total_hrs
                gap_hrs           = round(max(0.0, required_hrs - total_hrs), 1)
                enough            = total_hrs >= required_hrs
                pct               = min(100, round(total_hrs / required_hrs * 100)) if required_hrs > 0 else 100

                # Trend
                trend = ""
                if n_sessions >= 2:
                    scores_list = sdf["score"].tolist()
                    slope_val   = scores_list[-1] - scores_list[0]
                    trend = f"📈 +{slope_val:.0f}pts" if slope_val > 0 else f"📉 {slope_val:.0f}pts"

                bar_c  = "#10b981" if enough else ("#f59e0b" if gap_hrs < 2 else "#ef4444")
                status = "✅ Enough time!" if enough else f"⚠️ Need {gap_hrs}h more"
                subj_color = next((s.get("color","#00d4ff") for s in subjects
                                   if s["name"] == subj_name), "#00d4ff")

                if enough:
                    insight_text = "You're spending enough time — keep your consistency to maintain the score."
                else:
                    insight_text = (f"To reach {target:.0f}%, you need approximately "
                                   f"{required_hrs}h total. Currently at {total_hrs}h "
                                   f"— study {gap_hrs}h more on this subject.")

                st.markdown(f"""
                <div style="background:var(--sur2);border:1px solid var(--brd);
                            border-left:3px solid {subj_color};border-radius:12px;
                            padding:14px 16px;margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;
                                align-items:flex-start;margin-bottom:8px;">
                        <div>
                            <span style="font-family:Syne;font-weight:700;
                                         color:{subj_color};font-size:14px;">{subj_name}</span>
                            <span style="font-size:10px;color:var(--muted);margin-left:8px;">
                                {n_sessions} sessions{' · ' + trend if trend else ''}
                            </span>
                        </div>
                        <span style="font-size:11px;color:{bar_c};font-weight:600;">{status}</span>
                    </div>
                    <div style="display:flex;gap:20px;margin-bottom:10px;flex-wrap:wrap;">
                        <div>
                            <div style="font-size:9px;color:var(--muted);text-transform:uppercase;
                                        letter-spacing:1px;">Time Spent</div>
                            <div style="font-family:'DM Mono',monospace;font-size:18px;
                                        color:{bar_c};font-weight:600;">{total_hrs}h</div>
                        </div>
                        <div>
                            <div style="font-size:9px;color:var(--muted);text-transform:uppercase;
                                        letter-spacing:1px;">ML Required</div>
                            <div style="font-family:'DM Mono',monospace;font-size:18px;
                                        color:var(--txt);font-weight:600;">{required_hrs}h</div>
                        </div>
                        <div>
                            <div style="font-size:9px;color:var(--muted);text-transform:uppercase;
                                        letter-spacing:1px;">Avg Score</div>
                            <div style="font-family:'DM Mono',monospace;font-size:18px;
                                        color:var(--acc);font-weight:600;">{avg_score}%</div>
                        </div>
                        <div>
                            <div style="font-size:9px;color:var(--muted);text-transform:uppercase;
                                        letter-spacing:1px;">Target</div>
                            <div style="font-family:'DM Mono',monospace;font-size:18px;
                                        color:var(--acc3);font-weight:600;">{target:.0f}%</div>
                        </div>
                    </div>
                    <div style="height:6px;background:var(--sur);border-radius:100px;overflow:hidden;">
                        <div style="width:{pct}%;height:100%;
                                    background:linear-gradient(90deg,{bar_c},{bar_c}aa);
                                    border-radius:100px;transition:width .5s;"></div>
                    </div>
                    <div style="display:flex;justify-content:space-between;margin-top:4px;">
                        <span style="font-size:10px;color:var(--muted);">
                            Progress to required hours
                        </span>
                        <span style="font-family:'DM Mono',monospace;font-size:10px;
                                     color:{bar_c};">{pct}%</span>
                    </div>
                    <div style="margin-top:8px;padding:8px 10px;background:var(--sur);
                                border-radius:8px;font-size:11px;color:var(--muted);">
                        🤖 <b style="color:var(--txt);">ML Insight:</b> {insight_text}
                    </div>
                </div>
                """, unsafe_allow_html=True)
