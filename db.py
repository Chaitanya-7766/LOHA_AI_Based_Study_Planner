import os
from supabase import create_client, Client
import streamlit as st

SUPABASE_URL = "https://xntagxcagezzncqnqxkb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhudGFneGNhZ2V6em5jcW5xeGtiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTgwODIzMTAsImV4cCI6MjA3MzY1ODMxMH0.-BiPqlT23VNLfdeO5SiTeScHiQfdptN7BzoQk6120so"

@st.cache_resource
def get_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def _uid():
    return st.session_state.get("user_id")

def _with_user(payload: dict) -> dict:
    uid = _uid()
    return {**payload, "user_id": uid} if uid else dict(payload)

# ── Study Plans ──────────────────────────────────────────────
def save_study_plan(plan: dict):
    sb = get_supabase()
    if sb:
        sb.table("study_plans").insert(_with_user(plan)).execute()

def get_all_plans():
    sb = get_supabase()
    if sb:
        query = sb.table("study_plans").select("*")
        if _uid():
            query = query.eq("user_id", _uid())
        res = query.order("created_at", desc=True).execute()
        return res.data
    return []

# User profile
def save_profile(profile: dict):
    sb = get_supabase()
    uid = _uid()
    if sb and uid:
        payload = {
            "id": uid,
            "full_name": profile.get("full_name"),
            "daily_hours": profile.get("daily_hours"),
            "target_score": profile.get("target_score"),
            "exam_date": profile.get("exam_date"),
            "peak_time": profile.get("peak_time"),
            "learning_style": profile.get("learning_style"),
        }
        sb.table("profiles").upsert(payload, on_conflict="id").execute()

# Subjects
def save_subject(subject: dict):
    sb = get_supabase()
    uid = _uid()
    if not (sb and uid and subject.get("name")):
        return
    payload = {
        "user_id": uid,
        "name": subject.get("name"),
        "icon": subject.get("icon", "📚"),
        "color": subject.get("color", "#00d4ff"),
        "target_score": subject.get("target_score", 80),
        "avg_score": subject.get("avg_score", 0),
        "session_count": subject.get("session_count", 0),
        "test_count": subject.get("test_count", 0),
        "topics": subject.get("topics", "—"),
    }
    existing = sb.table("subjects").select("id").eq("user_id", uid).eq("name", payload["name"]).limit(1).execute().data
    if existing:
        sb.table("subjects").update(payload).eq("id", existing[0]["id"]).execute()
    else:
        sb.table("subjects").insert(payload).execute()

def delete_subject(name: str):
    sb = get_supabase()
    uid = _uid()
    if sb and uid and name:
        sb.table("subjects").delete().eq("user_id", uid).eq("name", name).execute()

# ── Progress ─────────────────────────────────────────────────
def save_progress(entry: dict):
    sb = get_supabase()
    if sb:
        sb.table("progress").insert(_with_user(entry)).execute()

def get_progress():
    sb = get_supabase()
    if sb:
        query = sb.table("progress").select("*")
        if _uid():
            query = query.eq("user_id", _uid())
        res = query.order("date", desc=False).execute()
        return res.data
    return []

# Schedule slots
def save_schedule_slots(slots: list):
    sb = get_supabase()
    uid = _uid()
    if not (sb and uid and slots):
        return
    dates = sorted({s.get("slot_date") for s in slots if s.get("slot_date")})
    if dates:
        sb.table("schedule_slots").delete().eq("user_id", uid).in_("slot_date", dates).execute()
    rows = []
    for slot in slots:
        subj = slot.get("subjects") or {}
        rows.append({
            "user_id": uid,
            "slot_date": slot.get("slot_date"),
            "start_time": slot.get("start_time"),
            "end_time": slot.get("end_time"),
            "status": slot.get("status", "scheduled"),
            "priority": slot.get("priority", 1),
            "subject_name": slot.get("subject_name") or subj.get("name", ""),
            "subject_icon": slot.get("subject_icon") or subj.get("icon", "📚"),
            "subject_color": slot.get("subject_color") or subj.get("color", "#00d4ff"),
        })
    if rows:
        sb.table("schedule_slots").insert(rows).execute()

# ── Chat History ──────────────────────────────────────────────
def save_chat(msg: dict):
    sb = get_supabase()
    if sb:
        sb.table("chat_history").insert(_with_user(msg)).execute()

def get_chat_history():
    sb = get_supabase()
    if sb:
        query = sb.table("chat_history").select("*")
        if _uid():
            query = query.eq("user_id", _uid())
        res = query.order("created_at", desc=False).limit(50).execute()
        return res.data
    return []
