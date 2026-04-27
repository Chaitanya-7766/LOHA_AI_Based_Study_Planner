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

# ── Study Plans ──────────────────────────────────────────────
def save_study_plan(plan: dict):
    sb = get_supabase()
    if sb:
        sb.table("study_plans").insert(plan).execute()

def get_all_plans():
    sb = get_supabase()
    if sb:
        res = sb.table("study_plans").select("*").order("created_at", desc=True).execute()
        return res.data
    return []

# ── Progress ─────────────────────────────────────────────────
def save_progress(entry: dict):
    sb = get_supabase()
    if sb:
        sb.table("progress").insert(entry).execute()

def get_progress():
    sb = get_supabase()
    if sb:
        res = sb.table("progress").select("*").order("date", desc=False).execute()
        return res.data
    return []

# ── Chat History ──────────────────────────────────────────────
def save_chat(msg: dict):
    sb = get_supabase()
    if sb:
        sb.table("chat_history").insert(msg).execute()

def get_chat_history():
    sb = get_supabase()
    if sb:
        res = sb.table("chat_history").select("*").order("created_at", desc=False).limit(50).execute()
        return res.data
    return []
