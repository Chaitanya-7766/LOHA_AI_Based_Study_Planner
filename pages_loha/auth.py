import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import db

# ── Colours used when rebuilding subjects ────────────────────────────
COLS = ['#00d4ff','#7c3aed','#f59e0b','#10b981','#ef4444','#a78bfa','#f97316','#38bdf8']

# ─────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────

def show_auth():

    # 🔥 If user exists → go to app
    if st.session_state.get("user"):
        return True

    # 🔥 If just logged out → show login
    if st.session_state.get("_force_logout"):
        st.session_state.pop("_force_logout", None)
        _render_auth_ui()
        return False

    # 🔁 Restore session (Supabase)
    if _restore_session():
        return True

    # 🧾 Default → show login
    _render_auth_ui()
    return False


def signout():
    try:
        sb = db.get_supabase()
        if sb:
            sb.auth.sign_out()
    except:
        pass

    # ✅ Clear session
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    # ✅ Force logout flag
    st.session_state["_force_logout"] = True

    st.rerun()


# ─────────────────────────────────────────────────────────────────────
# SESSION RESTORE  ← fixes the refresh-logs-you-out bug
# ─────────────────────────────────────────────────────────────────────

def _restore_session():
    """
    Ask Supabase for the currently active session.
    If a JWT is still valid, restore the user without showing the login form.
    """
    try:
        sb = db.get_supabase()
        if not sb:
            return False
        session = sb.auth.get_session()
        if session and session.user:
            user  = session.user
            name  = (user.user_metadata or {}).get("full_name") or user.email.split("@")[0]
            uid   = user.id
            # Only reload from DB if it's a fresh browser load (no subjects yet)
            if not st.session_state.get("user_id"):
                _boot_user(user, name)
            return True
    except:
        pass
    return False


# ─────────────────────────────────────────────────────────────────────
# LOGIN / SIGNUP UI
# ─────────────────────────────────────────────────────────────────────

def _render_auth_ui():
    st.markdown("""
    <style>
    [data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"] { display:none !important; }
    .block-container { padding:0 !important; max-width:100% !important; }
    .auth-logo-block { margin-top:8vh; margin-bottom:24px; text-align:center; }
    .auth-logo {
        font-family:'Syne',sans-serif;
        font-size:40px;
        font-weight:800;
        background:linear-gradient(135deg,var(--acc),var(--acc2));
        -webkit-background-clip:text;
        -webkit-text-fill-color:transparent;
    }
    .auth-subtitle {
        font-size:10px;
        color:var(--muted);
        letter-spacing:4px;
        text-transform:uppercase;
        margin-top:8px;
    }
    .amsg-e {
        border-radius:8px; padding:10px 14px; font-size:12px; margin-bottom:12px;
        background:rgba(239,68,68,.1); border:1px solid rgba(239,68,68,.3); color:#ef4444;
    }
    .amsg-s {
        border-radius:8px; padding:10px 14px; font-size:12px; margin-bottom:12px;
        background:rgba(16,185,129,.1); border:1px solid rgba(16,185,129,.3); color:#10b981;
    }
    .auth-divider { text-align:center; font-size:11px; color:var(--muted); margin-top:14px; }
    </style>
    """, unsafe_allow_html=True)

    if "auth_tab" not in st.session_state:
        st.session_state.auth_tab = "signin"

    _, auth_col, _ = st.columns([1.55, 1, 1.55])
    with auth_col:
        st.markdown("""
        <div class="auth-logo-block">
            <div class="auth-logo">LOHA</div>
            <div class="auth-subtitle">AI Study Planner</div>
        </div>
        """, unsafe_allow_html=True)

        is_signin = st.session_state.auth_tab == "signin"
        t1, t2 = st.columns(2)
        if t1.button("Sign In", key="tab_si", use_container_width=True,
                     type="primary" if is_signin else "secondary"):
            st.session_state.auth_tab = "signin"; st.rerun()
        if t2.button("Create Account", key="tab_su", use_container_width=True,
                     type="primary" if not is_signin else "secondary"):
            st.session_state.auth_tab = "signup"; st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if is_signin:
            _signin_form()
        else:
            _signup_form()


def _signin_form():
    msg = st.empty()
    email = st.text_input("Email", placeholder="you@example.com", key="signin_email")
    password = st.text_input("Password", type="password", placeholder="••••••••", key="signin_password")
    submitted = st.button("Sign In →", key="signin_submit", use_container_width=True)

    if submitted:
        if not email or not password:
            msg.markdown('<div class="amsg-e">Please fill in all fields.</div>', unsafe_allow_html=True)
            return
        with st.spinner("Signing in..."):
            result = _do_signin(email.strip(), password)
        if result["success"]:
            _boot_user(result["user"], result.get("name", email.split("@")[0]))
            st.session_state["_auth_success"] = True
            for k in ["auth_tab", "signin_email", "signin_password"]:
                st.session_state.pop(k, None)
            st.rerun()
        else:
            msg.markdown(f'<div class="amsg-e">{result["error"]}</div>', unsafe_allow_html=True)

    st.markdown('<div class="auth-divider">Don\'t have an account? Click <b style="color:var(--acc);">Create Account</b> above</div>', unsafe_allow_html=True)


def _signup_form():
    msg = st.empty()
    name = st.text_input("Full Name", placeholder="e.g. Chaitanya Kumar", key="signup_name")
    email = st.text_input("Email", placeholder="you@example.com", key="signup_email")
    password = st.text_input("Password", type="password", placeholder="Min 6 characters", key="signup_password")
    submitted = st.button("Create Account →", key="signup_submit", use_container_width=True)

    if submitted:
        if not name or not email or not password:
            msg.markdown('<div class="amsg-e">Please fill in all fields.</div>', unsafe_allow_html=True)
            return
        if len(password) < 6:
            msg.markdown('<div class="amsg-e">Password must be at least 6 characters.</div>', unsafe_allow_html=True)
            return
        with st.spinner("Creating your account..."):
            result = _do_signup(email.strip(), password, name.strip())
        if result["success"]:
            if result.get("needs_confirmation"):
                msg.markdown('<div class="amsg-s">Account created! Check your email to confirm, then sign in.</div>', unsafe_allow_html=True)
                st.session_state.auth_tab = "signin"; st.rerun()
            else:
                _boot_user(result["user"], name.strip())
                # Clear auth UI state so no login portal flashes on the next render
                st.session_state["_auth_success"] = True
                for k in ["auth_tab", "signup_name", "signup_email", "signup_password"]:
                    st.session_state.pop(k, None)
                st.rerun()
        else:
            msg.markdown(f'<div class="amsg-e">{result["error"]}</div>', unsafe_allow_html=True)

    st.markdown('<div class="auth-divider">Already have an account? Click <b style="color:var(--acc);">Sign In</b> above</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# SUPABASE CALLS
# ─────────────────────────────────────────────────────────────────────

def _do_signin(email, password):
    try:
        sb = db.get_supabase()
        if not sb:
            return _demo_login(email)
        res  = sb.auth.sign_in_with_password({"email": email, "password": password})
        user = res.user
        if not user:
            return {"success": False, "error": "Invalid email or password."}
        name = (user.user_metadata or {}).get("full_name") or email.split("@")[0]
        return {"success": True, "user": user, "name": name}
    except Exception as e:
        err = str(e).lower()
        if "invalid" in err or "credentials" in err:
            return {"success": False, "error": "Invalid email or password."}
        return _demo_login(email)


def _do_signup(email, password, name):
    try:
        sb = db.get_supabase()
        if not sb:
            return _demo_signup(email, name)
        res  = sb.auth.sign_up({"email": email, "password": password,
                                 "options": {"data": {"full_name": name}}})
        user = res.user
        if not user:
            return {"success": False, "error": "Signup failed. Please try again."}
        if not res.session:
            return {"success": True, "user": user, "needs_confirmation": True}
        return {"success": True, "user": user}
    except Exception as e:
        err = str(e).lower()
        if "already" in err or "exists" in err:
            return {"success": False, "error": "Email already registered. Please sign in."}
        return _demo_signup(email, name)


def _demo_login(email):
    users = st.session_state.get("_demo_users", {})
    if email in users:
        return {"success": True, "user": {"id": email, "email": email},
                "name": users[email]["name"]}
    return {"success": False, "error": "Account not found. Please create an account first."}


def _demo_signup(email, name):
    if "_demo_users" not in st.session_state:
        st.session_state._demo_users = {}
    if email in st.session_state._demo_users:
        return {"success": False, "error": "Email already registered. Please sign in."}
    st.session_state._demo_users[email] = {"name": name, "email": email}
    return {"success": True, "user": {"id": email, "email": email}}


# ─────────────────────────────────────────────────────────────────────
# SESSION BOOT & DATA LOAD
# ─────────────────────────────────────────────────────────────────────

def _boot_user(user, name):
    uid = getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else name)
    # Don't re-boot if same user already loaded
    if st.session_state.get("user_id") == uid and st.session_state.get("user"):
        return
    st.session_state.update({
        "user":          user,
        "user_id":       uid,
        "user_name":     name,
        "user_email":    getattr(user, "email", None) or (user.get("email","") if isinstance(user, dict) else ""),
        "user_avatar":   name[0].upper() if name else "U",
        # Start empty — will be filled by _load_user_data
        "subjects":      [],
        "progress_log":  [],
        "profile":       {"full_name": name},
        "schedule_slots":[],
        "week_offset":   0,
        "chat_messages": [],
    })
    for k in ["weak_results","sr_results","pred_results","study_time_result","ai_ins"]:
        st.session_state.pop(k, None)
    _load_user_data(uid, name)


def _load_user_data(uid, name):
    """Load ALL persisted data for this user from Supabase."""
    try:
        sb = db.get_supabase()
        if not sb:
            return
    except:
        return

    # ── 1. Profile ────────────────────────────────────────────────────
    try:
        rows = sb.table("profiles").select("*").eq("id", uid).execute().data
        if rows:
            p = rows[0]
            st.session_state.profile = {
                "full_name":      p.get("full_name", name),
                "daily_hours":    p.get("daily_hours", 4),
                "target_score":   p.get("target_score", 80),
                "exam_date":      p.get("exam_date", ""),
                "peak_time":      p.get("peak_time", "evening"),
                "learning_style": p.get("learning_style", "practice"),
            }
            if p.get("onboarding_done"):
                st.session_state.onboarding_done = True
    except:
        pass

    # ── 2. Subjects ───────────────────────────────────────────────────
    try:
        subjs = sb.table("subjects").select("*").eq("user_id", uid)\
                   .order("created_at").execute().data or []
        if subjs:
            st.session_state.subjects = [
                {
                    "name":          s["name"],
                    "icon":          s.get("icon", "📚"),
                    "color":         s.get("color", COLS[i % len(COLS)]),
                    "target_score":  s.get("target_score", 80),
                    "avg_score":     s.get("avg_score", 0),
                    "session_count": s.get("session_count", 0),
                    "test_count":    s.get("test_count", 0),
                    "topics":        s.get("topics", "—"),
                    "subject_id":    s.get("id", s["name"]),
                }
                for i, s in enumerate(subjs)
            ]
    except:
        pass

    # ── 3. Progress (all records) ─────────────────────────────────────
    try:
        prog = sb.table("progress").select("*")\
                  .eq("user_id", uid).order("date").execute().data or []
        if prog:
            st.session_state.progress_log = prog
    except:
        pass

    # ── 4. Schedule slots ─────────────────────────────────────────────
    try:
        from datetime import date, timedelta
        past   = (date.today() - timedelta(days=60)).strftime("%Y-%m-%d")
        future = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
        slots  = sb.table("schedule_slots").select("*")\
                    .eq("user_id", uid)\
                    .gte("slot_date", past)\
                    .lte("slot_date", future)\
                    .order("slot_date").order("start_time").execute().data or []
        if slots:
            st.session_state.schedule_slots = [
                {
                    "slot_date":     s.get("slot_date", ""),
                    "start_time":    s.get("start_time", ""),
                    "end_time":      s.get("end_time", ""),
                    "status":        s.get("status", "scheduled"),
                    "priority":      s.get("priority", 1),
                    "subject_name":  s.get("subject_name", ""),
                    "subject_icon":  s.get("subject_icon", "📚"),
                    "subject_color": s.get("subject_color", "#00d4ff"),
                    "subjects": {
                        "name":  s.get("subject_name", ""),
                        "icon":  s.get("subject_icon", "📚"),
                        "color": s.get("subject_color", "#00d4ff"),
                    },
                    "_id": s.get("id"),
                }
                for s in slots
            ]
    except:
        pass

    # ── 5. Chat history ───────────────────────────────────────────────
    try:
        chats = sb.table("chat_history").select("*")\
                   .eq("user_id", uid).order("created_at").limit(100).execute().data or []
        if chats:
            st.session_state.chat_messages = [
                {"role": c.get("role", "assistant"), "content": c.get("message", "")}
                for c in chats
            ]
    except:
        pass


def _clear_session():
    for k in ["user","user_id","user_name","user_email","user_avatar",
              "subjects","progress_log","profile","schedule_slots",
              "weak_results","sr_results","pred_results","study_time_result",
              "ai_ins","chat_messages","week_offset","auth_tab",
              "onboarding_done","onboarding_step","onboarding_skipped"]:
        st.session_state.pop(k, None)
