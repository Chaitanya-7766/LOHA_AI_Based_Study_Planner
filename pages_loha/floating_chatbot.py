import json
import os
import urllib.error
import urllib.request
from html import escape

import streamlit as st


# Gemini API Configuration
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
DEFAULT_MODEL = "gemini-2.0-flash"


def _api_key():
    # Try environment variable first (most reliable)
    # 1) session (entered in-app during this Streamlit session)
    try:
        s = st.session_state.get("GEMINI_API_KEY")
        if s:
            return s
    except Exception:
        pass

    # 2) environment variable
    env_key = os.getenv("GEMINI_API_KEY")
    if env_key:
        return env_key
    
    # Try Streamlit secrets
    try:
        secrets_key = st.secrets.get("GEMINI_API_KEY")
        if secrets_key:
            return secrets_key
    except Exception as e:
        pass
    
    return None


def _model_name():
    # Try environment variable first
    env_model = os.getenv("GEMINI_MODEL")
    if env_model:
        return env_model
    
    # Try Streamlit secrets
    try:
        secrets_model = st.secrets.get("GEMINI_MODEL")
        if secrets_model:
            return secrets_model
    except Exception:
        pass
    
    return DEFAULT_MODEL


def _profile_context():
    profile = st.session_state.get("profile", {})
    subjects = st.session_state.get("subjects", [])
    subject_bits = []
    for s in subjects[:8]:
        subject_bits.append(
            f"{s.get('name', 'Subject')}: avg {s.get('avg_score', 0)}%, "
            f"target {s.get('target_score', 80)}%"
        )
    return {
        "name": st.session_state.get("user_name", "student"),
        "exam_date": profile.get("exam_date", "not set"),
        "daily_hours": profile.get("daily_hours", "not set"),
        "subjects": "; ".join(subject_bits) or "No subjects added yet",
    }


def _fallback_response(prompt, reason=None):
    low = prompt.lower()
    if "schedule" in low:
        msg = "Add or review your subjects first, then generate this week's plan from Schedule. Prioritize subjects with the largest target gap."
    elif "weak" in low or "improve" in low:
        msg = "Pick one weak subject, study one topic for 25 minutes, then log the session with a self-score. LOHA can use that data for better insights."
    elif "exam" in low:
        msg = "For exam prep, focus on weak topics first, revise active notes daily, and practice past questions under time limits."
    else:
        msg = "I can help with study planning, weak topics, revision, focus sessions, and exam prep. Add your Gemini API key to enable smarter live responses."

    if reason:
        return f"{msg}\n\n[LOHA fallback reply: {reason}]"
    return msg


def ask_gemini(prompt):
    key = _api_key()
    if not key:
        return _fallback_response(prompt)

    ctx = _profile_context()
    
    # Build the system + context message for Gemini
    system_prompt = (
        f"You are LOHA's floating study assistant. Give concise, practical study advice. "
        f"Use the student's profile when useful. Avoid long answers unless asked.\n\n"
        f"Student Profile:\n"
        f"Name: {ctx['name']}\n"
        f"Exam Date: {ctx['exam_date']}\n"
        f"Daily Study Hours: {ctx['daily_hours']}\n"
        f"Subjects: {ctx['subjects']}"
    )
    
    # Build conversation history
    history = st.session_state.get("floating_chat_messages", [])[-6:]
    conversation = []
    
    for msg in history:
        role = "user" if msg.get("role") == "user" else "model"
        conversation.append({
            "role": role,
            "parts": [{"text": msg.get("content", "")}]
        })
    
    # Add current user message
    conversation.append({
        "role": "user",
        "parts": [{"text": prompt}]
    })
    
    # Prepare Gemini API request
    body = json.dumps({
        "contents": conversation,
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 420,
        }
    }).encode("utf-8")

    # Construct URL with API key
    url = f"{GEMINI_URL}?key={key}"
    
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=25) as res:
            data = json.loads(res.read().decode("utf-8"))
        
        # Extract text from Gemini response
        if "candidates" in data and len(data["candidates"]) > 0:
            candidate = data["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                if len(candidate["content"]["parts"]) > 0:
                    return candidate["content"]["parts"][0]["text"].strip()
        
        return _fallback_response(prompt, "No valid Gemini response.")
        
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")[:180]
        if e.code == 429:
            return _fallback_response(prompt, "Gemini quota exceeded. using local assistant fallback.")
        return _fallback_response(prompt, f"Gemini HTTP error {e.code}.")
    except Exception as e:
        return _fallback_response(prompt, f"Connection error: {str(e)[:100]}")


def _ensure_state():
    if "floating_chat_open" not in st.session_state:
        st.session_state.floating_chat_open = False
    if "floating_chat_messages" not in st.session_state:
        st.session_state.floating_chat_messages = [
            {
                "role": "assistant",
                "content": "Hi, I am LOHA. Ask me about your schedule, weak subjects, focus sessions, or exam prep.",
            }
        ]
    if "floating_chat_last_prompt" not in st.session_state:
        st.session_state.floating_chat_last_prompt = ""
    if "floating_chat_input_nonce" not in st.session_state:
        st.session_state.floating_chat_input_nonce = 0


def render(current_page="Dashboard"):
    _ensure_state()

    # Hidden widget used to persist drag position between reruns
    st.text_input("", key="floating_chat_position", label_visibility="collapsed")

    # Allow user to enter an API key for this session only (won't be saved to repo)
    if not _api_key():
        with st.expander("Set Gemini API key (session only)", expanded=False):
            entered = st.text_input("Paste Gemini API key", type="password", key="floating_chat_enter_key")
            if st.button("Save API key for session", key="floating_chat_save_key"):
                if entered and entered.strip():
                    st.session_state["GEMINI_API_KEY"] = entered.strip()
                    st.experimental_rerun()

    st.markdown("""
    <style>
    .st-key-loha_floating_chatbot {
        position: fixed !important;
        top: var(--loha-chat-top, auto) !important;
        left: var(--loha-chat-left, auto) !important;
        bottom: var(--loha-chat-bottom, 22px) !important;
        right: var(--loha-chat-right, 22px) !important;
        width: auto !important;
        max-width: none !important;
        z-index: 999999 !important;
        background: rgba(17, 24, 39, .95);
        border: 1px solid rgba(139, 92, 246, .75);
        border-radius: 13px;
        box-shadow: 0 0 0 1px rgba(99,102,241,.18), 0 24px 90px rgba(0,0,0,.46);
        padding: 20px;
        backdrop-filter: blur(18px);
        overflow: auto !important;
        display: flex !important;
        flex-direction: column !important;
        cursor: grab;
    }
    .st-key-loha_floating_chatbot:has(.loha-chat-closed) {
        width: 132px;
        padding: 0;
        border: 0;
        background: transparent;
        box-shadow: none;
        backdrop-filter: none;
        overflow: visible;
    }
    .st-key-loha_floating_chatbot > div,
    .st-key-loha_floating_chatbot [data-testid="stVerticalBlock"] {
        flex: 1 !important;
        min-height: 0 !important;
        overflow: visible !important;
    }
    input[id*="floating_chat_position"] {
        display: none !important;
    }
    .st-key-loha_floating_chatbot .stButton > button {
        width: 100% !important;
        min-height: 42px !important;
        border-radius: 8px !important;
    }
    .loha-chat-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(139, 92, 246, .35);
        padding-bottom: 12px;
        margin-bottom: 14px;
        flex-shrink: 0;
    }
    .loha-chat-title {
        font-family: Syne, sans-serif;
        font-size: 18px;
        font-weight: 800;
        color: var(--txt);
    }
    .loha-chat-status {
        font-family: 'DM Mono', monospace;
        font-size: 9px;
        color: var(--acc4);
        letter-spacing: 1px;
    }
    .loha-chat-messages {
        height: auto !important;
        flex: 1 !important;
        min-height: 400px;
        max-height: 80vh;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        padding-right: 8px;
        margin-bottom: 14px;
    }
    .loha-msg {
        border: 1px solid var(--brd);
        border-radius: 10px;
        padding: 9px 11px;
        margin-bottom: 8px;
        font-size: 12px;
        line-height: 1.5;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    .loha-msg-user {
        background: linear-gradient(135deg, var(--acc2), var(--acc));
        color: white;
        margin-left: 38px;
        border-color: transparent;
    }
    .loha-msg-assistant {
        background: var(--sur2);
        color: var(--txt);
        margin-right: 28px;
    }
    @media (max-width: 700px) {
        .st-key-loha_floating_chatbot {
            width: auto !important;
            left: 2.5% !important;
            right: 2.5% !important;
        }
        .st-key-loha_floating_chatbot:has(.loha-chat-closed) {
            width: 132px !important;
        }
        .loha-chat-messages {
            max-height: 75vh;
        }
    }
    </style>
    <script>
    (() => {
        const widget = document.querySelector(".st-key-loha_floating_chatbot");
        const input = document.querySelector('input[id*="floating_chat_position"]');
        if (!widget || !input) {
            return;
        }

        const parsePosition = (value) => {
            const result = {};
            value.split(';').forEach((part) => {
                const [key, rawValue] = part.split(':');
                if (key && rawValue) {
                    result[key.trim()] = rawValue.trim();
                }
            });
            return result;
        };

        const setCssVars = (pos) => {
            if (pos.top) document.documentElement.style.setProperty('--loha-chat-top', pos.top);
            if (pos.left) document.documentElement.style.setProperty('--loha-chat-left', pos.left);
            if (pos.bottom) document.documentElement.style.setProperty('--loha-chat-bottom', pos.bottom);
            if (pos.right) document.documentElement.style.setProperty('--loha-chat-right', pos.right);
        };

        const saved = parsePosition(input.value || '');
        setCssVars(saved);

        const handle = widget.querySelector('.loha-chat-head') || widget;
        let dragging = false;
        let offsetX = 0;
        let offsetY = 0;

        handle.style.cursor = 'grab';
        handle.style.touchAction = 'none';

        handle.addEventListener('pointerdown', (event) => {
            if (event.target.tagName.toLowerCase() === 'button') {
                return;
            }
            dragging = true;
            const rect = widget.getBoundingClientRect();
            offsetX = event.clientX - rect.left;
            offsetY = event.clientY - rect.top;
            handle.setPointerCapture(event.pointerId);
            handle.style.cursor = 'grabbing';
        });

        document.addEventListener('pointermove', (event) => {
            if (!dragging) {
                return;
            }
            const x = Math.max(0, event.clientX - offsetX);
            const y = Math.max(0, event.clientY - offsetY);
            widget.style.left = `${x}px`;
            widget.style.top = `${y}px`;
            widget.style.right = 'auto';
            widget.style.bottom = 'auto';
        });

        const stopDragging = () => {
            if (!dragging) {
                return;
            }
            dragging = false;
            handle.style.cursor = 'grab';
            input.value = `top:${widget.style.top};left:${widget.style.left};bottom:auto;right:auto;`;
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
        };

        handle.addEventListener('pointerup', stopDragging);
        document.addEventListener('pointerup', stopDragging);
        document.addEventListener('pointercancel', stopDragging);
    })();
    </script>
    """, unsafe_allow_html=True)

    with st.container(key="loha_floating_chatbot"):
        if not st.session_state.floating_chat_open:
            st.markdown('<div class="loha-chat-closed"></div>', unsafe_allow_html=True)
            if st.button("Ask LOHA", key="floating_chat_open_btn", use_container_width=True):
                st.session_state.floating_chat_open = True
                st.rerun()
            return

        status = "GEMINI READY" if _api_key() else "SET API KEY"
        st.markdown(f"""
        <div class="loha-chat-head">
            <div class="loha-chat-title">LOHA Assistant</div>
            <div class="loha-chat-status">{status}</div>
        </div>
        """, unsafe_allow_html=True)

        messages_html = ""
        for msg in st.session_state.floating_chat_messages[-8:]:
            cls = "loha-msg-user" if msg["role"] == "user" else "loha-msg-assistant"
            content = escape(str(msg["content"])).replace("\n", "<br>")
            messages_html += f'<div class="loha-msg {cls}">{content}</div>'
        st.markdown(f'<div class="loha-chat-messages">{messages_html}</div>', unsafe_allow_html=True)

        input_key = f"floating_chat_input_{st.session_state.floating_chat_input_nonce}"
        prompt = st.text_area(
            "Ask LOHA",
            key=input_key,
            placeholder="Ask about your schedule, weak subjects, or exam prep...",
            height=80,
            label_visibility="collapsed",
        )
        c1, c2 = st.columns([1, 1])
        if c1.button("Send", key="floating_chat_send", use_container_width=True):
            clean = prompt.strip()
            if clean:
                st.session_state.floating_chat_messages.append({"role": "user", "content": clean})
                with st.spinner("LOHA is thinking..."):
                    reply = ask_gemini(clean)
                st.session_state.floating_chat_messages.append({"role": "assistant", "content": reply})
                st.session_state.floating_chat_input_nonce += 1
                st.rerun()
        if c2.button("Close", key="floating_chat_close", use_container_width=True, type="secondary"):
            st.session_state.floating_chat_open = False
            st.rerun()
