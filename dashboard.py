import streamlit as st
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from streamlit_autorefresh import st_autorefresh
from notion_client import Client
from dotenv import load_dotenv
import os
import io

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# Research Engine
from research_engine import generate_research_package, generate_research_timeline

# ---------------- CONFIG ---------------- #

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

notion = Client(auth=NOTION_TOKEN) if NOTION_TOKEN else None

IST = timezone(timedelta(hours=5, minutes=30))

st.set_page_config(page_title="AgentX Ultimate", layout="wide")
st_autorefresh(interval=30000, key="refresh")

# ---------------- SESSION STATE INIT ---------------- #

if "research_data" not in st.session_state:
    st.session_state.research_data = None

if "timeline" not in st.session_state:
    st.session_state.timeline = None

if "last_topic" not in st.session_state:
    st.session_state.last_topic = ""

# ---------------- NAVIGATION ---------------- #

menu = st.sidebar.radio(
    "🚀 AgentX Navigation",
    ["Dashboard", "Research Copilot", "Rewards", "Streak", "Invite Friends"]
)

# ---------------- LOAD EVENTS ---------------- #

try:
    with open("events.json", "r") as f:
        events = json.load(f)
except:
    events = []

data = []
for idx, event in enumerate(events):
    dt = datetime.fromisoformat(event["datetime"])
    data.append({
        "ID": idx,
        "Title": event["title"],
        "DateTime": dt,
        "Status": "Done" if event["reminded"] else "Pending"
    })

df = pd.DataFrame(data)
now = datetime.now(IST)

# ================= DASHBOARD ================= #

if menu == "Dashboard":

    st.title("🤖 AgentX Control Center")

    total = len(df)
    done = len(df[df["Status"] == "Done"])
    pending = total - done

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Events", total)
    col2.metric("Completed", done)
    col3.metric("Pending", pending)

    progress = done / total if total else 0
    st.subheader("🎯 Productivity Progress")
    st.progress(progress)

    if not df.empty:
        upcoming = df[df["DateTime"] >= now].sort_values("DateTime")
        st.subheader("📅 Upcoming Events")
        st.dataframe(upcoming, width="stretch")
    else:
        st.info("No events available.")

# ================= RESEARCH COPILOT ================= #

elif menu == "Research Copilot":

    st.title("🔬 AgentX Research Copilot")

    topic = st.text_input(
        "Enter Research Topic",
        value=st.session_state.last_topic
    )

    if st.button("Generate Research Package"):

        if topic:
            with st.spinner("Generating research framework..."):
                st.session_state.research_data = generate_research_package(topic)
                st.session_state.timeline = generate_research_timeline(topic)
                st.session_state.last_topic = topic
        else:
            st.warning("Please enter a topic.")

    research_data = st.session_state.research_data
    timeline = st.session_state.timeline

    if research_data:

        st.success("Research Generated Successfully!")

        # -------- DISPLAY -------- #

        st.subheader("📖 Overview")
        st.write(research_data.get("overview", ""))

        st.subheader("🧱 Outline")
        for item in research_data.get("outline", []):
            st.write("•", item)

        st.subheader("📚 Key Concepts")
        for concept in research_data.get("key_concepts", []):
            st.write("•", concept)

        st.subheader("❓ Research Questions")
        for q in research_data.get("research_questions", []):
            st.write("•", q)

        st.subheader("📑 Citations")
        for c in research_data.get("citations", []):
            st.write("•", c)

        if timeline:
            st.subheader("📅 7-Day Plan")
            for day, task in timeline.items():
                st.write(f"**{day}** — {task}")

        # -------- SAVE TO NOTION -------- #

        if notion and NOTION_DATABASE_ID:
            if st.button("💾 Save to Notion"):
                try:
                    notion.pages.create(
                        parent={"database_id": NOTION_DATABASE_ID},
                        properties={
                            "Name": {
                                "title": [
                                    {"text": {"content": st.session_state.last_topic}}
                                ]
                            }
                        }
                    )
                    st.success("Saved to Notion!")
                except Exception as e:
                    st.error(f"Notion Error: {e}")

        # -------- EXPORT PDF -------- #

        pdf_buffer = io.BytesIO()

        doc = SimpleDocTemplate(pdf_buffer)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph(st.session_state.last_topic, styles["Heading1"]))
        elements.append(Spacer(1, 0.3 * inch))

        elements.append(Paragraph("Overview:", styles["Heading2"]))
        elements.append(Paragraph(research_data.get("overview", ""), styles["Normal"]))
        elements.append(Spacer(1, 0.3 * inch))

        for section in ["outline", "key_concepts", "research_questions", "citations"]:
            elements.append(Paragraph(section.replace("_"," ").title(), styles["Heading2"]))
            for item in research_data.get(section, []):
                elements.append(Paragraph(f"• {item}", styles["Normal"]))
            elements.append(Spacer(1, 0.2 * inch))

        if timeline:
            elements.append(Paragraph("7-Day Plan", styles["Heading2"]))
            for day, task in timeline.items():
                elements.append(Paragraph(f"{day}: {task}", styles["Normal"]))

        doc.build(elements)
        pdf_buffer.seek(0)

        st.download_button(
            label="📄 Download Research PDF",
            data=pdf_buffer,
            file_name=f"{st.session_state.last_topic.replace(' ','_')}_research.pdf",
            mime="application/pdf"
        )

# ================= REWARDS ================= #

elif menu == "Rewards":
    st.title("🏆 Rewards Center")

# ================= STREAK ================= #

elif menu == "Streak":
    st.title("🔥 Daily Streak")

# ================= INVITE ================= #

elif menu == "Invite Friends":
    st.title("👥 Invite Friends")

st.caption("AgentX Ultimate • Productivity OS 🔥")