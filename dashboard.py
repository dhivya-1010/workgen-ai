import streamlit as st
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from streamlit_autorefresh import st_autorefresh
from notion_client import Client
from dotenv import load_dotenv
import os

# ---------------- CONFIG ---------------- #

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = "31461e925a9480d29a9fefc14d9ac655"

notion = Client(auth=NOTION_TOKEN) if NOTION_TOKEN else None

IST = timezone(timedelta(hours=5, minutes=30))

st.set_page_config(page_title="AgentX Ultimate", layout="wide")

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

# ---------------- NAVIGATION ---------------- #

menu = st.sidebar.radio(
    "🚀 AgentX Navigation",
    ["Dashboard", "Rewards", "Streak", "Invite Friends"]
)

# ---------------- LOAD EVENTS ---------------- #

try:
    with open("events.json", "r") as f:
        events = json.load(f)
except:
    st.warning("No events.json found")
    st.stop()

if not events:
    st.info("No events available")
    st.stop()

data = []
for idx, event in enumerate(events):
    dt = datetime.fromisoformat(event["datetime"])
    data.append({
        "ID": idx,
        "Title": event["title"],
        "DateTime": dt,
        "Date": dt.date(),
        "Time": dt.time(),
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

# ================= REWARDS ================= #

elif menu == "Rewards":

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