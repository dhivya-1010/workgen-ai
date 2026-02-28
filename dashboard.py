import streamlit as st
import json
import os
from datetime import datetime

st.set_page_config(page_title="AgentX Dashboard", layout="wide")

st.title("🤖 AgentX - AI Meeting Assistant")

st.markdown("---")

# ------------------ Load Events ------------------ #

def load_events():
    if os.path.exists("events.json"):
        with open("events.json", "r") as f:
            return json.load(f)
    return []

events = load_events()

# ------------------ Stats ------------------ #

col1, col2 = st.columns(2)

col1.metric("Total Meetings", len(events))

upcoming = [e for e in events if not e["reminded"]]
col2.metric("Pending Reminders", len(upcoming))

st.markdown("---")

# ------------------ Event Table ------------------ #

st.subheader("Upcoming Meetings")

if events:
    for event in events:
        event_time = datetime.fromisoformat(event["datetime"])
        status = "Pending" if not event["reminded"] else "✅ Reminded"

        with st.container():
            st.write(f"### {event['title']}")
            st.write(f"{event_time.strftime('%Y-%m-%d %H:%M')}")
            st.write(f"Status: {status}")
            st.markdown("---")
else:
    st.info("No meetings found yet.")

st.markdown("### Controls")

if st.button("Fetch Emails Now"):
    st.success("Run main.py in terminal to fetch new meetings.")