from __future__ import print_function
from win10toast import ToastNotifier

import os
import base64
import json
import ollama
import time

from notion_client import Client
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from datetime import datetime, timedelta, timezone


# ------------------ LOAD ENV ------------------ #

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = "31461e925a9480d29a9fefc14d9ac655"

notion = Client(auth=NOTION_TOKEN) if NOTION_TOKEN else None

# India timezone
IST = timezone(timedelta(hours=5, minutes=30))

# Windows notifier
toaster = ToastNotifier()

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar'
]


# ------------------ AUTH ------------------ #

def get_credentials():
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds


# ------------------ AI EXTRACTION ------------------ #

def extract_meeting_details(email_text):

    prompt = f"""
Extract meeting details from this email.

Return ONLY valid JSON in this format:

{{
  "title": "",
  "date": "YYYY-MM-DD",
  "time": "HH:MM",
  "duration": ""
}}

If no meeting is found, return:
{{ "meeting": "no" }}

Email:
{email_text}
"""

    response = ollama.chat(
        model="gemma:2b",
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0}
    )

    raw_output = response["message"]["content"].strip()

    try:
        return json.loads(raw_output)
    except:
        start = raw_output.find("{")
        end = raw_output.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(raw_output[start:end+1])
            except:
                return {"meeting": "no"}
        return {"meeting": "no"}


# ------------------ LOCAL STORAGE ------------------ #

def save_event_locally(title, start_time):

    event_data = {
        "title": title,
        "datetime": start_time.isoformat(),
        "reminded": False
    }

    if os.path.exists("events.json"):
        with open("events.json", "r") as f:
            events = json.load(f)
    else:
        events = []

    events.append(event_data)

    with open("events.json", "w") as f:
        json.dump(events, f, indent=2)


# ------------------ NOTION SYNC ------------------ #

def add_to_notion(meeting, start_time):

    if not notion:
        print("⚠️ Notion token missing. Skipping Notion sync.")
        return

    try:
        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Name": {
                    "title": [{"text": {"content": meeting["title"]}}]
                },
                "Date": {
                    "date": {"start": start_time.isoformat()}
                },
                "Status": {
                    "select": {"name": "Pending"}
                },
                "Source": {
                    "rich_text": [{"text": {"content": "Created by AgentXX"}}]
                }
            }
        )
        print("📝 Added to Notion")
    except Exception as e:
        print("❌ Notion Error:", e)


# ------------------ CALENDAR ------------------ #

def add_to_calendar(meeting):

    if (
        "meeting" in meeting or
        not meeting.get("date") or
        not meeting.get("time")
    ):
        print("Invalid meeting data. Skipping.")
        return

    creds = get_credentials()
    calendar_service = build('calendar', 'v3', credentials=creds)

    if not meeting.get("title"):
        meeting["title"] = "Meeting"

    try:
        start_time = datetime.strptime(
            f"{meeting['date']} {meeting['time']}",
            "%Y-%m-%d %H:%M"
        )
        start_time = start_time.replace(tzinfo=IST)

    except:
        print("Time format issue. Skipping event.")
        return

    if start_time < datetime.now(IST):
        print("Past date detected. Skipping.")
        return

    duration_minutes = 60
    if meeting.get("duration"):
        try:
            duration_minutes = int(meeting["duration"])
        except:
            pass

    end_time = start_time + timedelta(minutes=duration_minutes)

    event = {
        'summary': meeting['title'],
        'description': "Created automatically by AgentXX",
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'Asia/Kolkata',
        },
    }

    calendar_service.events().insert(
        calendarId='primary',
        body=event
    ).execute()

    print("✅ Event added to Google Calendar")

    save_event_locally(meeting["title"], start_time)
    add_to_notion(meeting, start_time)


# ------------------ READ EMAILS ------------------ #

def read_emails():

    print("Fetching emails...")

    creds = get_credentials()
    gmail_service = build('gmail', 'v1', credentials=creds)

    results = gmail_service.users().messages().list(
        userId='me',
        maxResults=5
    ).execute()

    messages = results.get('messages', [])

    print("Messages found:", len(messages))

    for msg in messages:
        msg_data = gmail_service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='full'
        ).execute()

        parts = msg_data['payload'].get('parts', [])

        for part in parts:
            if part['mimeType'] == 'text/plain':
                data = part['body']['data']
                text = base64.urlsafe_b64decode(data).decode()

                print("\n----- EMAIL -----\n")
                print(text)

                meeting = extract_meeting_details(text)

                print("\n===== EXTRACTED MEETING DATA =====\n")
                print(json.dumps(meeting, indent=2))

                add_to_calendar(meeting)


# ------------------ REMINDER SYSTEM ------------------ #

def check_reminders():

    if not os.path.exists("events.json"):
        return

    with open("events.json", "r") as f:
        events = json.load(f)

    now = datetime.now(IST)
    updated = False

    for event in events:

        event_time = datetime.fromisoformat(event["datetime"])

        # ensure timezone-aware
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=IST)

        reminder_time = event_time - timedelta(hours=1)

        if not event["reminded"] and reminder_time <= now < event_time:

            print("\n🔔 REMINDER 🔔")
            print(f"Meeting: {event['title']}")
            print(f"Time: {event_time.strftime('%Y-%m-%d %H:%M')}")
            print("-----------------------------")

            toaster.show_toast(
                "🔔 AgentX Reminder",
                f"{event['title']} at {event_time.strftime('%H:%M')}",
                duration=10
            )

            event["reminded"] = True
            updated = True

    if updated:
        with open("events.json", "w") as f:
            json.dump(events, f, indent=2)


def reminder_loop():
    print("\n⏳ Reminder system running...\n")
    while True:
        check_reminders()
        time.sleep(60)


# ------------------ MAIN ------------------ #

if __name__ == '__main__':
    read_emails()
    reminder_loop()