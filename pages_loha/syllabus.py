import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from pages_loha.ui_helpers import page_header, section_header
from nlp_engine import parse_syllabus, generate_topic_summary

def show():
    st.markdown(page_header("Syllabus Parser", "NLP-powered topic extraction & difficulty scoring"), unsafe_allow_html=True)
    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)

    tab1,tab2 = st.tabs(["✏️ Paste Syllabus Text","📤 Upload .txt File"])
    raw_text = ""
    with tab1:
        raw_text_input = st.text_area("Paste syllabus here",height=220,
            placeholder="Unit 1: Introduction to Machine Learning\n- Supervised Learning: Regression, Classification\n- Neural Networks, Backpropagation\nUnit 2: Deep Learning\n- CNNs, RNNs, Transformers",
            label_visibility="collapsed",key="syl_ta")
        if raw_text_input: raw_text = raw_text_input
    with tab2:
        uploaded = st.file_uploader("Upload .txt file",type=["txt"],key="syl_up")
        if uploaded:
            raw_text = uploaded.read().decode("utf-8",errors="ignore")
            st.success(f"✅ File loaded: {uploaded.name}")

    subject_override = st.text_input("Subject Name (optional — override auto-detected)", placeholder="e.g. Machine Learning", key="syl_subj")

    if st.button("🔍 Parse & Analyze Syllabus", use_container_width=True, key="parse_btn"):
        if not raw_text:
            st.warning("⚠️ Please enter or upload syllabus text first.")
            return
        with st.spinner("🧠 Running NLP analysis..."):
            result = parse_syllabus(raw_text)
        detected = subject_override if subject_override else result["detected_subject"]
        st.success(f"✅ Detected Subject: **{detected}** — Found **{result['total_topics']}** topics")

        # Stat cards
        cards_html = f"""
        <div class='cgrid'>
            <div class='scard sc'><div class='sico'>📚</div><div class='slbl'>Topics Found</div><div class='sval'>{result['total_topics']}</div></div>
            <div class='scard sp'><div class='sico'>🔴</div><div class='slbl'>High Priority</div><div class='sval' style='color:#ef4444'>{result['high_priority']}</div></div>
            <div class='scard sa'><div class='sico'>🟡</div><div class='slbl'>Medium Priority</div><div class='sval'>{result['medium_priority']}</div></div>
            <div class='scard sg'><div class='sico'>🟢</div><div class='slbl'>Low Priority</div><div class='sval' style='color:var(--acc4)'>{result['low_priority']}</div></div>
        </div>"""
        st.markdown(cards_html, unsafe_allow_html=True)

        # Pie chart
        pie_data = pd.DataFrame({"Priority":["High","Medium","Low"],"Count":[result["high_priority"],result["medium_priority"],result["low_priority"]]})
        fig = px.pie(pie_data,names="Priority",values="Count",color="Priority",
            color_discrete_map={"High":"#ef4444","Medium":"#f59e0b","Low":"#10b981"},hole=0.45)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",font_color="#5a7090",legend=dict(orientation="h",x=0.25,y=-0.1),margin=dict(t=20,b=20))
        fig.update_traces(textfont_color="white")
        c1,c2,c3 = st.columns([1,2,1])
        with c2: st.plotly_chart(fig,use_container_width=True)

        # Topic cards
        st.markdown(section_header("📚 Extracted Topics", "NLP"), unsafe_allow_html=True)
        tier_map = {"High":("#ef4444","🔴"),"Medium":("#f59e0b","🟡"),"Low":("#10b981","🟢")}
        for t in result["topics"]:
            diff = t["difficulty_score"]
            c,dot = tier_map.get(t["priority"],("#5a7090","⚪"))
            stars = "★"*round(diff)+"☆"*(5-round(diff))
            summary = generate_topic_summary(t["name"])
            kws = " ".join([f"<span style='background:var(--sur2);border:1px solid var(--brd);border-radius:20px;padding:2px 8px;font-size:10px;color:var(--muted);margin:1px;'>{k}</span>" for k in t.get("keywords",[])[:4]])
            st.markdown(f"""
            <div class='ic' style='border-left:3px solid {c};margin-bottom:8px;'>
                <div style='flex:1;'>
                    <div style='display:flex;justify-content:space-between;align-items:center;'>
                        <span style='font-family:Syne;color:var(--txt);font-weight:600;font-size:0.9rem;'>{t["name"]}</span>
                        <div style='text-align:right;'>
                            <span style='color:{c};font-size:0.9rem;'>{stars}</span>
                            <span style='font-size:9px;padding:2px 8px;border-radius:20px;background:{c}22;color:{c};border:1px solid {c}44;margin-left:5px;'>{t["priority"]}</span>
                        </div>
                    </div>
                    <div style='font-size:11px;color:var(--muted);margin-top:3px;'>{summary}</div>
                    <div style='margin-top:4px;'>{kws}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Export
        topics_df = pd.DataFrame(result["topics"])[["name","difficulty_score","priority"]]
        topics_df.columns = ["Topic","Difficulty Score","Priority"]
        st.download_button("⬇️ Download Topics CSV", topics_df.to_csv(index=False), f"{detected}_topics.csv","text/csv")
        st.session_state["parsed_topics"] = result["topics"]
        st.session_state["parsed_subject"] = detected
        st.info("💡 Topics saved! Go to **Study Planner** to use them directly.")
