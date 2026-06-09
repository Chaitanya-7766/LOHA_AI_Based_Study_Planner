import streamlit as st
import sys, os, json, urllib.request, urllib.error
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pages_loha.ui_helpers import page_header, section_header
import db
from html import escape

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
DEFAULT_MODEL = "gemini-2.0-flash"

def _api_key():
    # Try environment variable first (most reliable)
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

def ask_gemini(prompt):
    """Send message to Gemini API and get response."""
    key = _api_key()
    if not key:
        return "⚠️ No Gemini API key found. Please add your GEMINI_API_KEY to environment variables or Streamlit secrets to enable AI responses."

    ctx = _profile_context()
    
    # Build the system + context message for Gemini
    system_prompt = (
        f"You are LOHA's AI study assistant. You provide concise, practical study advice tailored to the student's needs. "
        f"Be encouraging, use emojis when appropriate, and keep responses focused and actionable.\n\n"
        f"Student Profile:\n"
        f"Name: {ctx['name']}\n"
        f"Exam Date: {ctx['exam_date']}\n"
        f"Daily Study Hours: {ctx['daily_hours']}\n"
        f"Subjects: {ctx['subjects']}"
    )
    
    # Build conversation history
    history = st.session_state.get("chat_messages", [])[-6:]
    conversation = []
    
    for msg in history:
        if msg.get("role") in ["user", "assistant"]:
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
            "maxOutputTokens": 512,
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
        
        return "No response from Gemini. Try again!"
        
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")[:200]
        return f"❌ Gemini API Error: {detail}"
    except Exception as e:
        return f"⚠️ Connection Error: {str(e)[:100]}. Please check your API key and internet connection."

def show():
    st.markdown(page_header("AI Chatbot", "Powered by Gemini API"), unsafe_allow_html=True)
    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)
    
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": "👋 **Hi! I'm LOHA**, your AI-powered study assistant. Ask me anything about study planning, weak subjects, exam prep, time management, or specific topics. I'll provide personalized advice based on your profile."
            }
        ]

    # Chat history panel
    st.markdown(section_header("🤖 LOHA Study Assistant", "AI-Powered Chatbot"), unsafe_allow_html=True)
    
    # Display messages
    for msg in st.session_state.chat_messages:
        if msg["role"] == "user":
            st.markdown(
                f"<div style='display:flex;justify-content:flex-end;margin-bottom:10px;'>"
                f"<div style='background:linear-gradient(135deg,var(--acc2),var(--acc));color:white;border-radius:18px 18px 4px 18px;padding:12px 14px;max-width:75%;font-size:13px;line-height:1.5;'>"
                f"{escape(msg['content'])}"
                f"</div></div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div style='display:flex;justify-content:flex-start;margin-bottom:10px;'>"
                f"<div style='background:var(--sur2);border:1px solid var(--brd);color:var(--txt);border-radius:18px 18px 18px 4px;padding:12px 14px;max-width:75%;font-size:13px;line-height:1.6;'>"
                f"{msg['content']}"
                f"</div></div>",
                unsafe_allow_html=True
            )

    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
    
    # Quick action buttons
    st.markdown(
        "<div style='font-size:10px;color:var(--muted);margin-bottom:8px;text-transform:uppercase;letter-spacing:1px;'>💡 Quick Questions:</div>",
        unsafe_allow_html=True
    )
    qcols = st.columns(4)
    quick_qs = [
        "How to study ML?",
        "Pomodoro technique?",
        "Exam prep tips",
        "Stay motivated?"
    ]
    for i, q in enumerate(quick_qs):
        if qcols[i].button(q, key=f"qq_{i}", use_container_width=True):
            st.session_state.chat_messages.append({"role": "user", "content": q})
            with st.spinner("🤔 LOHA is thinking..."):
                response = ask_gemini(q)
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
            try:
                db.save_chat({"role": "user", "message": q})
                db.save_chat({"role": "assistant", "message": response})
            except:
                pass
            st.rerun()

    st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
    
    # User input
    user_input = st.chat_input("Ask LOHA anything about studying...", key="chatbot_input")
    if user_input:
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        
        with st.spinner("🤔 LOHA is thinking..."):
            response = ask_gemini(user_input)
        
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        try:
            db.save_chat({"role": "user", "message": user_input})
            db.save_chat({"role": "assistant", "message": response})
        except:
            pass
        st.rerun()

    st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History", key="chat_clear", use_container_width=False):
        st.session_state.chat_messages = [st.session_state.chat_messages[0]]
        st.rerun()
