import streamlit as st
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from streamlit_autorefresh import st_autorefresh
from notion_client import Client
from dotenv import load_dotenv
import os
<<<<<<< HEAD
import io

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# Research Engine
from research_engine import generate_research_package, generate_research_timeline
=======
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580

# ---------------- CONFIG ---------------- #

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
<<<<<<< HEAD
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
=======
NOTION_DATABASE_ID = "31461e925a9480d29a9fefc14d9ac655"
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580

notion = Client(auth=NOTION_TOKEN) if NOTION_TOKEN else None

IST = timezone(timedelta(hours=5, minutes=30))

st.set_page_config(page_title="AgentX Ultimate", layout="wide")
<<<<<<< HEAD
st_autorefresh(interval=30000, key="refresh")

# ---------------- SESSION STATE INIT ---------------- #

if "research_data" not in st.session_state:
    st.session_state.research_data = None

if "timeline" not in st.session_state:
    st.session_state.timeline = None

if "last_topic" not in st.session_state:
    st.session_state.last_topic = ""
=======

# Auto refresh every 30 sec
st_autorefresh(interval=30000, key="refresh")

# ---------------- STYLE ---------------- #

st.markdown("""
<style>
body {background-color:#0f172a; color:white;}
h1,h2,h3 {color:#00F5FF;}
.stButton>button {
    background-color:#1e293b;
    color:white;
    border-radius:10px;
    height:3em;
}
</style>
""", unsafe_allow_html=True)
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580

# ---------------- NAVIGATION ---------------- #

menu = st.sidebar.radio(
    "🚀 AgentX Navigation",
<<<<<<< HEAD
    ["Dashboard", "Research Copilot", "Rewards", "Streak", "Invite Friends"]
=======
    ["Dashboard", "Rewards", "Streak", "Invite Friends"]
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
)

# ---------------- LOAD EVENTS ---------------- #

try:
    with open("events.json", "r") as f:
        events = json.load(f)
except:
<<<<<<< HEAD
    events = []
=======
    st.warning("No events.json found")
    st.stop()

if not events:
    st.info("No events available")
    st.stop()
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580

data = []
for idx, event in enumerate(events):
    dt = datetime.fromisoformat(event["datetime"])
    data.append({
        "ID": idx,
        "Title": event["title"],
        "DateTime": dt,
<<<<<<< HEAD
=======
        "Date": dt.date(),
        "Time": dt.time(),
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
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

<<<<<<< HEAD
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
=======
    st.divider()

    # FILTER
    st.sidebar.header("Filters")
    type_filter = st.sidebar.selectbox(
        "Filter by Type",
        ["All"] + list(df["Title"].unique())
    )

    display_df = df
    if type_filter != "All":
        display_df = df[df["Title"] == type_filter]

    # UPCOMING
    st.subheader("📅 Upcoming Events")
    upcoming = display_df[display_df["DateTime"] >= now].sort_values("DateTime")
    st.dataframe(upcoming[["Title","DateTime","Status"]], use_container_width=True)

    # STATUS TOGGLE
    st.subheader("✔ Update Event Status")
    selected_id = st.selectbox("Select Event", df["ID"])

    if st.button("Mark as Done"):
        events[selected_id]["reminded"] = True
        with open("events.json","w") as f:
            json.dump(events,f,indent=2)
        st.success("🔥 Event Completed!")

    # DELETE DUPLICATES
    st.subheader("🗑 Remove Duplicate Events")
    if st.button("Clean Duplicates"):
        unique = {}
        cleaned = []
        for event in events:
            key = (event["title"], event["datetime"])
            if key not in unique:
                unique[key] = True
                cleaned.append(event)
        with open("events.json","w") as f:
            json.dump(cleaned,f,indent=2)
        st.success("Duplicates Removed 🔥")

    # COUNTDOWN
    st.subheader("⏳ Next Event Countdown")
    if not upcoming.empty:
        next_event = upcoming.iloc[0]
        time_left = next_event["DateTime"] - now
        st.success(f"Next: {next_event['Title']}")
        st.write(f"Starts at: {next_event['DateTime']}")
        st.write(f"Time left: {str(time_left).split('.')[0]}")
    else:
        st.info("No upcoming events")

    # CHART
    st.subheader("📊 Event Distribution")
    st.bar_chart(df["Title"].value_counts())

    # NOTION STATUS
    st.subheader("🔗 Notion Sync Status")
    if notion:
        try:
            response = notion.databases.query(database_id=NOTION_DATABASE_ID)
            st.success(f"Connected to Notion • {len(response['results'])} entries")
        except:
            st.error("Notion connection failed")
    else:
        st.warning("Notion token missing")
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580

# ================= REWARDS ================= #

elif menu == "Rewards":
<<<<<<< HEAD
    st.title("🏆 Rewards Center")

# ================= STREAK ================= #

elif menu == "Streak":
    st.title("🔥 Daily Streak")

# ================= INVITE ================= #

elif menu == "Invite Friends":
    st.title("👥 Invite Friends")

st.caption("AgentX Ultimate • Productivity OS 🔥")
=======

    st.title("🏆 Rewards Center")

    done_count = len(df[df["Status"]=="Done"])

    if done_count >= 100:
        badge = "🏆 LEGEND"
    elif done_count >= 30:
        badge = "🥇 GOLD"
    elif done_count >= 15:
        badge = "🥈 SILVER"
    elif done_count >= 5:
        badge = "🥉 BRONZE"
    else:
        badge = "⚡ Beginner"

    st.subheader(f"Your Badge: {badge}")
    st.write(f"Completed Events: {done_count}")

# ================= STREAK ================= #

elif menu == "Streak":

    st.title("🔥 Daily Streak")

    try:
        with open("streak.json","r") as f:
            streak_data = json.load(f)
    except:
        streak_data = {"count":0}

    st.metric("Current Streak", streak_data["count"])

    if st.button("Increase Streak (Demo)"):
        streak_data["count"] += 1
        with open("streak.json","w") as f:
            json.dump(streak_data,f)
        st.success("Streak Increased!")

# ================= INVITE ================= #

elif menu == "Invite Friends":

    st.title("👥 Invite Friends")

    st.write("Boost your productivity community!")

    email = st.text_input("Enter friend's email")

    if st.button("Send Invite"):
        st.success(f"Invitation sent to {email} 🚀")

    st.subheader("🎁 Referral Rewards")
    st.write("Invite 3 friends → Unlock Exclusive Theme")
    st.write("Invite 5 friends → Double Streak Bonus")

st.caption("AgentX Ultimate • Gamified Productivity Mode 🚀")
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
