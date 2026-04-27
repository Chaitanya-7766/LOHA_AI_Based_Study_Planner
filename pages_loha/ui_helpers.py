"""Reusable HTML snippets matching LOHA_index.html exactly"""
from datetime import datetime, date, timedelta

COLS = ['#00d4ff','#7c3aed','#f59e0b','#10b981','#ef4444','#a78bfa','#f97316','#38bdf8']
ICOS = ['📚','⚡','🧪','🧬','✍️','🔢','🎨','🌍']

def page_header(title: str, sub: str = "", exam_days=None):
    sub_text = sub or datetime.now().strftime("%A, %B %d %Y")
    exam_bar = ""
    if exam_days is not None:
        exam_bar = f"""
        <div class="exambar">
            <span style="color:var(--muted);font-size:10px;">Exam in</span>
            <span class="examval">{exam_days}</span>
            <span style="color:var(--muted);font-size:10px;">days</span>
        </div>"""
    return f"""
        <div class="hdr">
            <div><h1>{title}</h1><p>{sub_text}</p></div>
            {exam_bar}
        </div>
        """.strip()

def stat_card(ico, label, value, variant="c", sub=""):
    sub_html = f'<div class="schg">{sub}</div>' if sub else ""
    return f"""
    <div class="scard {variant}">
        <div class="sico">{ico}</div>
        <div class="slbl">{label}</div>
        <div class="sval">{value}</div>
        {sub_html}
    </div>"""

def panel_open(title, tag=""):
    tag_html = f'<span class="ptag">{tag}</span>' if tag else ""
    return f'<div class="panel"><div class="ph"><span class="ptitle">{title}</span>{tag_html}</div><div class="pb">'

def panel_close():
    return "</div></div>"

def section_header(title, tag=""):
    tag_html = f'<span class="ptag">{tag}</span>' if tag else ""
    return f'<div class="panel"><div class="ph"><span class="ptitle">{title}</span>{tag_html}</div></div>'

import html

def insight_card(icon, title, message, *args, style="i"):
    return f"""
    <div class="ic">
        <div>{icon}</div>
        <div>
            <div>{title}</div>
            <div>{html.escape(str(message))}</div>
        </div>
    </div>
    """.strip()

def subject_perf_bars(subjects):
    if not subjects:
        return '<div class="empty"><div class="empty-ico">📚</div>No subjects yet. Go to Setup.</div>'
    html = ""
    for i, s in enumerate(subjects):
        c  = s.get("color") or COLS[i % len(COLS)]
        sc = round(float(s.get("avg_score") or 0))
        note = " ⚠ Weak" if sc < 60 else (" ✓ Strong" if sc >= 85 else "")
        html += f"""
        <div class="si">
            <div class="sirow">
                <span class="siname"><span class="sidot" style="background:{c}"></span>{s.get('icon','📚')} {s['name']}</span>
                <span class="sipct">{sc}%{note}</span>
            </div>
            <div class="pbar"><div class="pfill" style="width:{sc}%;background:linear-gradient(90deg,{c},{c}99)"></div></div>
        </div>"""
    return html

def weak_warning(subjects):
    html = ""
    for s in subjects:
        if float(s.get("avg_score") or 0) < 60:
            html += f"""<div class="wa"><div style="font-size:17px">⚠️</div>
            <div><strong>{s['name']}</strong> is a weak area — avg {round(s.get('avg_score',0))}%.
            LOHA has boosted {s['name']} time in your schedule.</div></div>"""
    return html

def subject_grid(subjects):
    if not subjects:
        return '<div class="empty" style="grid-column:1/-1"><div class="empty-ico">📚</div>Add subjects in Setup to get started.</div>'
    html = ""
    for i, s in enumerate(subjects):
        c  = s.get("color") or COLS[i % len(COLS)]
        sc = round(float(s.get("avg_score") or 0))
        sc_color = "#ef4444" if sc < 60 else c
        html += f"""
        <div class="scrd" style="border-color:{c}44">
            <div style="font-size:20px;margin-bottom:7px">{s.get('icon', ICOS[i%len(ICOS)])}</div>
            <div style="font-family:Syne;font-size:13px;font-weight:700;color:{c};margin-bottom:2px">{s['name']}</div>
            <div style="font-size:10px;color:var(--muted);margin-bottom:8px">{s.get('topics','–')}</div>
            <div class="scbar"><div class="scfill" style="width:{sc}%;background:linear-gradient(90deg,{c},{c}77)"></div></div>
            <div style="display:flex;gap:8px;font-size:10px;color:var(--muted);">
                Score: <strong style="color:{sc_color}">{sc}%</strong>
                &nbsp;Sessions: <strong style="color:var(--txt)">{s.get('session_count',0)}</strong>
                &nbsp;Tests: <strong style="color:var(--txt)">{s.get('test_count',0)}</strong>
            </div>
        </div>"""
    return html

def schedule_slots_html(slots):
    if not slots:
        return '<div class="empty"><div class="empty-ico">📅</div>No schedule yet. Click "Generate Schedule" above.</div>'
    today = date.today().strftime("%Y-%m-%d")
    grouped = {}
    for s in slots:
        d = s.get("slot_date","")
        grouped.setdefault(d, []).append(s)
    html = ""
    for date_str, day_slots in sorted(grouped.items()):
        try:
            lbl = datetime.strptime(date_str,"%Y-%m-%d").strftime("%A, %b %d")
        except:
            lbl = date_str
        today_badge = '<span class="tbadge">TODAY</span>' if date_str == today else ""
        html += f'<div style="margin-bottom:16px"><div class="dlbl">{lbl}{today_badge}</div>'
        for sl in day_slots:
            subj    = sl.get("subjects") or {}
            c       = subj.get("color") or sl.get("subject_color","#00d4ff")
            start_t = (sl.get("start_time","") or "")[:5]
            end_t   = (sl.get("end_time","")   or "")[:5]
            status  = sl.get("status","scheduled")
            stc     = "#10b981" if status=="done" else ("#f59e0b" if status=="pending" else "#5a7090")
            name    = subj.get("name") or sl.get("subject_name","Study")
            icon    = subj.get("icon") or sl.get("subject_icon","📚")
            done_mark = " ✓" if status == "done" else ""
            html += f"""
            <div class="sslot">
                <span class="stime">{start_t} – {end_t}</span>
                <div class="sbar" style="border-color:{c}">
                    <span class="ssub">{icon} {name}{done_mark}</span>
                    <div style="display:flex;align-items:center;gap:5px;">
                        <span class="stg" style="background:{stc}22;color:{stc}">{status.upper()}</span>
                    </div>
                </div>
            </div>"""
        html += "</div>"    
    return html

def heatmap_html(logs):
    today = date.today()
    start = today - timedelta(days=55)
    daily = {}
    for l in logs:
        k = l.get("date","")
        if k:
            daily[k] = daily.get(k,0) + 1
    mx  = max(daily.values()) if daily else 1
    cur = start - timedelta(days=start.weekday())
    day_labels = ["M","T","W","T","F","S","S"]
    html = '<div style="display:flex;gap:9px;overflow-x:auto;padding-bottom:5px;">'
    while cur <= today:
        html += f'<div style="display:flex;flex-direction:column;gap:1px;"><div style="font-family:\'DM Mono\',monospace;font-size:9px;color:var(--muted);text-align:center;margin-bottom:3px;">{day_labels[cur.weekday()]}</div>'
        for i in range(7):
            cell = cur + timedelta(days=i)
            if cell > today:
                html += '<div class="hcell"></div>'
                continue
            k   = cell.strftime("%Y-%m-%d")
            cnt = daily.get(k,0)
            v   = 0 if cnt==0 else min(5, max(1, int(cnt/mx*5)))
            dv  = f'data-v="{v}"' if v else ""
            html += f'<div class="hcell" {dv} title="{k}: {cnt} sessions"></div>'
        html += "</div>"
        cur += timedelta(weeks=1)
    html += '</div>'
    html += """<div style="display:flex;align-items:center;gap:6px;margin-top:9px;">
        <span style="font-size:10px;color:var(--muted);">Less</span>
        <div style="width:12px;height:12px;border-radius:2px;background:var(--sur2);border:1px solid var(--brd);"></div>
        <div style="width:12px;height:12px;border-radius:2px;background:rgba(0,212,255,.15);"></div>
        <div style="width:12px;height:12px;border-radius:2px;background:rgba(0,212,255,.35);"></div>
        <div style="width:12px;height:12px;border-radius:2px;background:rgba(0,212,255,.6);"></div>
        <div style="width:12px;height:12px;border-radius:2px;background:var(--acc);"></div>
        <span style="font-size:10px;color:var(--muted);">More</span>
    </div>"""
    return html
