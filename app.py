import streamlit as st

if "user" not in st.session_state:
    st.session_state.user = None

st.set_page_config(
    page_title="LOHA – AI Study Planner",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Global CSS (matches LOHA_index.html exactly) ─────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@400;500&display=swap');

:root {
    --bg:#0b0f19;
    --sur:#111827;
    --sur2:#1f2937;
    --brd:#2d3748;

    --acc:#6366f1;      /* Indigo */
    --acc2:#8b5cf6;     /* Violet */
    --acc3:#f59e0b;     /* Amber */
    --acc4:#22c55e;     /* Green */

    --red:#ef4444;

    --txt:#f9fafb;
    --muted:#9ca3af;
}
*, *::before, *::after { box-sizing:border-box; }
html, body, [data-testid="stAppViewContainer"], .stApp {
    background:var(--bg) !important; color:var(--txt) !important;
    font-family:'DM Sans',sans-serif !important;
}
body::before {
    content:''; position:fixed; inset:0; pointer-events:none; z-index:0;
    background:radial-gradient(ellipse 800px 600px at 20% 10%,rgba(0,212,255,.04),transparent 60%),
               radial-gradient(ellipse 600px 500px at 80% 80%,rgba(124,58,237,.05),transparent 60%);
}
.grid-bg {
    position:fixed; inset:0; pointer-events:none; z-index:0;
    background-image:linear-gradient(rgba(0,212,255,.025) 1px,transparent 1px),
                     linear-gradient(90deg,rgba(0,212,255,.025) 1px,transparent 1px);
    background-size:60px 60px;
}
h1,h2,h3 { font-family:'Syne',sans-serif !important; }
.block-container { padding:0 !important; max-width:100% !important; }

/* SIDEBAR */
[data-testid="stSidebar"] {
    background:var(--sur) !important;
    border-right:1px solid var(--brd) !important;
    min-width:232px !important; max-width:232px !important;
}
[data-testid="stSidebar"] > div { padding:0 !important; background:var(--sur) !important; }
[data-testid="stSidebar"] * { color:var(--txt) !important; }
[data-testid="stSidebar"] .stRadio > label { display:none !important; }
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] { gap:2px !important; padding:0 10px !important; }
[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] {
    display:flex !important; align-items:center !important; gap:9px !important;
    padding:10px 12px !important; border-radius:9px !important;
    color:var(--muted) !important; font-size:13px !important; font-weight:500 !important;
    transition:all .2s !important; background:transparent !important;
    border:none !important; width:100% !important; position:relative !important;
}
[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:hover {
    color:var(--txt) !important; background:var(--sur2) !important;
}
[data-testid="stSidebar"] .stRadio label[aria-checked="true"] {
    color:var(--acc) !important; background:rgba(0,212,255,.08) !important;
}
[data-testid="stSidebar"] .stRadio label[aria-checked="true"]::before {
    content:''; position:absolute; left:0; top:50%; transform:translateY(-50%);
    width:3px; height:58%; background:var(--acc); border-radius:0 2px 2px 0;
}
[data-testid="stSidebar"] .stRadio input { display:none !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:var(--muted) !important; font-size:11px !important; }

/* INPUTS */
.stTextInput input, .stNumberInput input, .stTextArea textarea {
    background:var(--sur2) !important; border:1px solid var(--brd) !important;
    border-radius:10px !important; color:var(--txt) !important;
    font-family:'DM Sans',sans-serif !important; font-size:13px !important; padding:11px 14px !important;
}
.stTextInput input:focus,.stTextArea textarea:focus,.stNumberInput input:focus {
    border-color:var(--acc) !important; box-shadow:none !important;
}
.stTextInput input::placeholder,.stTextArea textarea::placeholder { color:var(--muted) !important; }
[data-baseweb="select"] > div { background:var(--sur2) !important; border-color:var(--brd) !important; border-radius:10px !important; }
[data-baseweb="select"] span { color:var(--txt) !important; }
[data-baseweb="popover"] ul { background:var(--sur2) !important; border-color:var(--brd) !important; }
[role="option"] { background:var(--sur2) !important; color:var(--txt) !important; }
[role="option"]:hover { background:var(--sur) !important; }
[data-testid="stDateInput"] input { background:var(--sur2) !important; border-color:var(--brd) !important; color:var(--txt) !important; border-radius:10px !important; }

/* BUTTONS */
.stButton > button {
    background:var(--acc) !important; color:var(--bg) !important;
    border:none !important; border-radius:9px !important;
    font-family:'DM Sans',sans-serif !important; font-size:12px !important;
    font-weight:700 !important; padding:9px 18px !important; transition:all .15s !important;
}
.stButton > button:hover {
    background:#00bcd4 !important; transform:translateY(-1px) !important;
    box-shadow:0 4px 20px rgba(0,212,255,.3) !important;
}
.stButton > button[kind="secondary"] {
    background:var(--sur2) !important; color:var(--txt) !important;
    border:1px solid var(--brd) !important;
}
.stButton > button[kind="secondary"]:hover { border-color:var(--acc) !important; color:var(--acc) !important; }
.stDownloadButton > button {
    background:var(--sur2) !important; color:var(--txt) !important;
    border:1px solid var(--brd) !important; border-radius:9px !important; font-size:12px !important;
}

/* SLIDERS */
[data-testid="stSlider"] [role="slider"] { background:var(--acc) !important; border-color:var(--acc) !important; }
[data-testid="stSlider"] > div > div > div > div { background:var(--acc) !important; }

/* FORMS */
[data-testid="stForm"] {
    background:var(--sur) !important; border:1px solid var(--brd) !important;
    border-radius:13px !important; padding:1.2rem 1.5rem !important;
}

/* EXPANDERS */
[data-testid="stExpander"] { background:var(--sur) !important; border:1px solid var(--brd) !important; border-radius:13px !important; }
[data-testid="stExpander"] summary { color:var(--txt) !important; font-family:'Syne',sans-serif !important; font-size:13px !important; font-weight:700 !important; }

/* TABS */
[data-testid="stTabs"] [role="tablist"] {
    background:var(--sur2) !important; border-radius:10px !important;
    padding:4px !important; gap:4px !important; border-bottom:none !important;
}
[data-testid="stTabs"] [role="tab"] {
    background:transparent !important; color:var(--muted) !important;
    border:none !important; border-radius:8px !important; font-size:12px !important;
    font-weight:500 !important; padding:8px 14px !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background:var(--acc) !important; color:var(--bg) !important; font-weight:700 !important;
}

/* DATAFRAMES */
[data-testid="stDataFrame"],.dvn-scroller { background:var(--sur) !important; border-radius:13px !important; }

/* ALERTS */
[data-testid="stAlert"] { border-radius:9px !important; }
.stSuccess { background:rgba(16,185,129,.1) !important; border-color:rgba(16,185,129,.3) !important; }
.stInfo    { background:rgba(0,212,255,.08) !important; border-color:rgba(0,212,255,.2) !important; }
.stWarning { background:rgba(245,158,11,.1) !important; border-color:rgba(245,158,11,.3) !important; }
.stError   { background:rgba(239,68,68,.1) !important; border-color:rgba(239,68,68,.3) !important; }

/* LABELS */
label[data-testid="stWidgetLabel"] {
    font-size:10px !important; color:var(--muted) !important;
    text-transform:uppercase !important; letter-spacing:1.5px !important; font-weight:500 !important;
}

/* HIDE STREAMLIT CHROME */
#MainMenu,footer,header,[data-testid="stToolbar"] { display:none !important; }

/* SCROLLBAR */
::-webkit-scrollbar { width:4px; height:4px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:var(--brd); border-radius:100px; }

/* SHARED COMPONENTS */
.panel { background:var(--sur); border:1px solid var(--brd); border-radius:13px; overflow:hidden; margin-bottom:14px; }
.ph { padding:13px 17px; border-bottom:1px solid var(--brd); display:flex; align-items:center; justify-content:space-between; }
.ptitle { font-family:'Syne',sans-serif; font-size:13px; font-weight:700; color:var(--txt); }
.ptag { font-size:9px; padding:3px 8px; border-radius:20px; background:rgba(0,212,255,.1); color:var(--acc); border:1px solid rgba(0,212,255,.2); font-family:'DM Mono',monospace; white-space:nowrap; }
.pb { padding:15px 17px; }

.scard { background:var(--sur); border:1px solid var(--brd); border-radius:13px; padding:17px; position:relative; overflow:hidden; transition:border-color .2s,transform .2s; }
.scard:hover { transform:translateY(-2px); }
.scard::after { content:''; position:absolute; top:0; left:0; right:0; height:2px; }
.sc{border-color:rgba(0,212,255,.3);} .sc::after{background:linear-gradient(90deg,transparent,var(--acc),transparent);}
.sp{border-color:rgba(124,58,237,.3);} .sp::after{background:linear-gradient(90deg,transparent,var(--acc2),transparent);}
.sa{border-color:rgba(245,158,11,.3);} .sa::after{background:linear-gradient(90deg,transparent,var(--acc3),transparent);}
.sg{border-color:rgba(16,185,129,.3);} .sg::after{background:linear-gradient(90deg,transparent,var(--acc4),transparent);}
.sico{font-size:18px;margin-bottom:8px;} .slbl{font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:4px;}
.sval{font-family:'Syne',sans-serif;font-size:23px;font-weight:700;line-height:1;}
.sc .sval{color:var(--acc);} .sp .sval{color:var(--acc2);} .sa .sval{color:var(--acc3);} .sg .sval{color:var(--acc4);}
.schg{font-size:10px;color:var(--muted);margin-top:4px;}

.ic { background:var(--sur2); border:1px solid var(--brd); border-radius:10px; padding:11px 13px; margin-bottom:8px; display:flex; align-items:flex-start; gap:9px; transition:border-color .2s; }
.ic:hover { border-color:rgba(0,212,255,.3); }
.icico { width:29px; height:29px; border-radius:7px; display:flex; align-items:center; justify-content:center; font-size:13px; flex-shrink:0; }
.iw{background:rgba(245,158,11,.15);} .ii{background:rgba(0,212,255,.12);} .ig{background:rgba(16,185,129,.12);}
.ictxt{font-size:12px;line-height:1.5;color:var(--txt);} .ictime{font-size:10px;color:var(--muted);margin-top:2px;}

.si{margin-bottom:12px;} .sirow{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;}
.siname{font-size:12.5px;font-weight:500;color:var(--txt);display:flex;align-items:center;gap:7px;}
.sidot{width:7px;height:7px;border-radius:50%;flex-shrink:0;} .sipct{font-family:'DM Mono',monospace;font-size:11px;color:var(--muted);}
.pbar{height:5px;background:var(--sur2);border-radius:100px;overflow:hidden;} .pfill{height:100%;border-radius:100px;}

.wa { background:rgba(239,68,68,.07); border:1px solid rgba(239,68,68,.2); border-radius:9px; padding:12px 14px; display:flex; align-items:center; gap:9px; margin-bottom:12px; font-size:12px; line-height:1.5; color:var(--txt); }

.scrd { background:var(--sur2); border:1px solid var(--brd); border-radius:12px; padding:15px; transition:all .2s; cursor:pointer; }
.scrd:hover { transform:translateY(-2px); box-shadow:0 8px 24px rgba(0,0,0,.3); }
.scbar{height:4px;background:var(--brd);border-radius:100px;overflow:hidden;margin-bottom:6px;} .scfill{height:100%;border-radius:100px;}

.hdr { padding:18px 30px; border-bottom:1px solid var(--brd); background:rgba(8,12,20,.85); backdrop-filter:blur(20px); display:flex; align-items:center; justify-content:space-between; position:sticky; top:0; z-index:10; }
.hdr h1{font-family:'Syne',sans-serif;font-size:17px;font-weight:700;color:var(--txt);margin:0;}
.hdr p{font-size:11px;color:var(--muted);margin:2px 0 0;}
.exambar{background:var(--sur2);border:1px solid var(--brd);border-radius:9px;padding:6px 12px;font-size:10px;display:flex;align-items:center;gap:7px;}
.examval{font-family:'DM Mono',monospace;font-size:15px;font-weight:500;color:var(--acc3);}

.sslot{display:flex;gap:10px;margin-bottom:6px;align-items:center;}
.stime{font-family:'DM Mono',monospace;font-size:10px;color:var(--muted);width:72px;flex-shrink:0;}
.sbar{flex:1;background:var(--sur2);border-radius:8px;padding:8px 11px;border-left:3px solid;display:flex;align-items:center;justify-content:space-between;cursor:pointer;}
.sbar:hover{background:rgba(255,255,255,.03);}
.ssub{font-size:12px;font-weight:500;color:var(--txt);} .stg{font-size:9px;padding:2px 7px;border-radius:20px;font-weight:600;} .sdur{font-family:'DM Mono',monospace;font-size:10px;color:var(--muted);}
.dlbl{font-family:'Syne',sans-serif;font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:7px;}
.tbadge{font-size:9px;background:rgba(0,212,255,.12);color:var(--acc);padding:2px 7px;border-radius:20px;margin-left:7px;}

.hcell{width:18px;height:18px;border-radius:3px;background:var(--sur2);cursor:pointer;transition:transform .15s;display:inline-block;margin:1px;}
.hcell:hover{transform:scale(1.3);}
.hcell[data-v="1"]{background:rgba(0,212,255,.15);} .hcell[data-v="2"]{background:rgba(0,212,255,.3);} .hcell[data-v="3"]{background:rgba(0,212,255,.5);} .hcell[data-v="4"]{background:rgba(0,212,255,.75);} .hcell[data-v="5"]{background:var(--acc);box-shadow:0 0 7px rgba(0,212,255,.4);}

.tdsp{font-family:'DM Mono',monospace;font-size:52px;font-weight:500;color:var(--acc);text-align:center;letter-spacing:4px;text-shadow:0 0 36px rgba(0,212,255,.4);padding:16px 0;}
.aidot{width:6px;height:6px;border-radius:50%;background:var(--acc4);box-shadow:0 0 7px var(--acc4);animation:pulse 2s infinite;display:inline-block;}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(.8)}}

.empty{text-align:center;padding:30px;color:var(--muted);font-size:12px;} .empty-ico{font-size:26px;margin-bottom:6px;}
.chip{display:inline-flex;align-items:center;gap:6px;background:var(--sur2);border:1px solid var(--brd);border-radius:20px;padding:5px 11px;font-size:12px;margin:2px;}
.content{padding:24px 30px;}

/* AUTH SPECIFIC */
.auth-page {
    display:flex; align-items:center; justify-content:center; min-height:85vh;
}
.acard {
    background:var(--sur); border:1px solid var(--brd); border-radius:20px;
    padding:44px; width:420px; max-width:95vw;
}
.alogo {
    font-family:'Syne',sans-serif; font-size:32px; font-weight:800;
    background:linear-gradient(135deg,var(--acc),var(--acc2));
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.asub { font-size:10px; color:var(--muted); letter-spacing:3px; text-transform:uppercase; margin-bottom:28px; margin-top:3px; }
.flbl { font-size:10px; color:var(--muted); text-transform:uppercase; letter-spacing:1.5px; margin-bottom:6px; display:block; font-weight:500; }
.amsg-e { border-radius:8px; padding:10px 14px; font-size:12px; margin-bottom:14px; background:rgba(239,68,68,.1); border:1px solid rgba(239,68,68,.3); color:#ef4444; }
.amsg-s { border-radius:8px; padding:10px 14px; font-size:12px; margin-bottom:14px; background:rgba(16,185,129,.1); border:1px solid rgba(16,185,129,.3); color:#10b981; }
</style>
<div class="grid-bg"></div>
""", unsafe_allow_html=True)

# ── Auth gate ────────────────────────────────────────────────────────
from pages_loha.auth import show_auth, signout

if not show_auth():
    st.stop()

# ── Onboarding (shown after first login) ────────────────────────────
from pages_loha.onboarding import should_show, show as show_onboarding
if should_show():
    show_onboarding()
    st.stop()

# ── Sidebar (only shown when logged in) ─────────────────────────────
PAGES = [
    ("⬡", "Dashboard"),
    ("📅", "Schedule"),
    ("📚", "Subjects"),
    ("⏱",  "Focus Timer"),
    ("🧠", "AI Insights"),
    ("📈", "Analytics"),
    ("⚙",  "Setup"),
]
page_names = [name for _, name in PAGES]
requested_page = st.query_params.get("page", "Dashboard")
if isinstance(requested_page, list):
    requested_page = requested_page[0] if requested_page else "Dashboard"
if requested_page not in page_names:
    requested_page = "Dashboard"
default_page_index = page_names.index(requested_page)

with st.sidebar:
    # Logo
    st.markdown("""
    <div style="padding:0 22px 22px;border-bottom:1px solid var(--brd);margin-bottom:18px;">
        <div style="font-family:Syne;font-size:24px;font-weight:800;letter-spacing:-1px;
                    background:linear-gradient(135deg,var(--acc),var(--acc2));
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">LOHA</div>
        <div style="font-size:9px;letter-spacing:3px;color:var(--muted);text-transform:uppercase;margin-top:2px;">
            AI Study Planner
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Nav
    page = st.radio("nav", [f"{ico}  {name}" for ico, name in PAGES],
                    index=default_page_index, label_visibility="collapsed")

    # User info + sign out at bottom
    uname  = st.session_state.get("user_name", "User")
    uemail = st.session_state.get("user_email", "")
    uav    = st.session_state.get("user_avatar", "U")

    st.markdown(f"""
    <div style="padding:14px 22px 0;border-top:1px solid var(--brd);margin-top:12px;">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:9px;">
            <div style="width:29px;height:29px;border-radius:50%;
                        background:linear-gradient(135deg,var(--acc2),var(--acc));
                        display:flex;align-items:center;justify-content:center;
                        font-family:Syne;font-size:12px;font-weight:700;color:#fff;">{uav}</div>
            <div>
                <div style="font-size:12px;font-weight:500;color:var(--txt);
                            white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:140px;">
                    {uname}
                </div>
                <div style="font-size:10px;color:var(--muted);
                            white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:140px;">
                    {uemail}
                </div>
            </div>
        </div>
        <div style="display:flex;align-items:center;gap:7px;font-size:10px;color:var(--muted);margin-bottom:10px;">
            <span class="aidot"></span> AI Engine Active
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Sign out", key="signout_btn", use_container_width=True, type="secondary"):
        signout()
        st.rerun()

# ── Page routing ─────────────────────────────────────────────────────
selected = page.split("  ", 1)[1] if "  " in page else page

if selected == "Dashboard":
    from pages_loha import dashboard;   dashboard.show()
elif selected == "Schedule":
    from pages_loha import schedule;    schedule.show()
elif selected == "Subjects":
    from pages_loha import subjects;    subjects.show()
elif selected == "Focus Timer":
    from pages_loha import focus;       focus.show()
elif selected == "AI Insights":
    from pages_loha import ai_insights; ai_insights.show()
elif selected == "Analytics":
    from pages_loha import analytics;   analytics.show()
elif selected == "Setup":
    from pages_loha import setup;       setup.show()

from pages_loha.floating_chatbot import render as render_floating_chatbot
render_floating_chatbot(selected)
