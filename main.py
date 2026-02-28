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


# ------------------ CONFIG ------------------ #

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = "31461e925a9480d29a9fefc14d9ac655"

notion = Client(auth=NOTION_TOKEN) if NOTION_TOKEN else None

IST = timezone(timedelta(hours=5, minutes=30))
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

def extract_email_intent(email_text):

    prompt = f"""
Classify and extract details.

Return ONLY valid JSON:

{{
  "type": "",
  "title": "",
  "date": "YYYY-MM-DD",
  "time": "HH:MM",
  "priority": "low/medium/high"
}}

If nothing found:
{{ "type": "none" }}

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
                return {"type": "none"}
        return {"type": "none"}


# ------------------ INTENT PROCESSOR ------------------ #

def process_intent(intent, original_text):

    detected_type = intent.get("type", "none")

    text_lower = original_text.lower()

    # 🔥 Strong fallback logic
    if "exam" in text_lower:
        detected_type = "exam"
    elif "meeting" in text_lower:
        detected_type = "meeting"
    elif "interview" in text_lower:
        detected_type = "interview"
    elif "assignment" in text_lower or "submission" in text_lower:
        detected_type = "task"
    elif "payment" in text_lower or "fees" in text_lower:
        detected_type = "payment"

    if detected_type == "none":
        print("No actionable content.")
        return

    if not intent.get("date"):
        print("No date found.")
        return

    try:
        if intent.get("time"):
            dt = datetime.strptime(
                f"{intent['date']} {intent['time']}",
                "%Y-%m-%d %H:%M"
            )
        else:
            dt = datetime.strptime(intent["date"], "%Y-%m-%d")

        dt = dt.replace(tzinfo=IST)

    except:
        print("Date format issue.")
        return

    if dt < datetime.now(IST):
        print("Past date. Skipping.")
        return

    title = intent.get("title") or detected_type.capitalize()

    print(f"🔥 Detected {detected_type} → {title}")

    create_calendar_event(title, dt, detected_type)


# ------------------ CALENDAR ------------------ #

def create_calendar_event(title, start_time, intent_type, duration_minutes=60):

    creds = get_credentials()
    calendar_service = build('calendar', 'v3', credentials=creds)

    end_time = start_time + timedelta(minutes=duration_minutes)

    color_map = {
        "meeting": "1",
        "task": "2",
        "exam": "11",
        "interview": "3",
        "payment": "6"
    }

    color_id = color_map.get(intent_type, "1")

    event = {
        'summary': title,
        'description': f"Created automatically by AgentX ({intent_type})",
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'Asia/Kolkata',
        },
        'colorId': color_id
    }

    calendar_service.events().insert(
        calendarId='primary',
        body=event
    ).execute()

    print("🎨 Added to Google Calendar")

    save_event_locally(title, start_time)
    add_to_notion(title, start_time)


# ------------------ NOTION ------------------ #

def add_to_notion(title, start_time):

    if not notion:
        return

    try:
        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Name": {
                    "title": [{"text": {"content": title}}]
                },
                "Date": {
                    "date": {"start": start_time.isoformat()}
                },
                "Status": {
                    "select": {"name": "Pending"}
                }
            }
        )
        print("📝 Added to Notion")
    except Exception as e:
        print("Notion Error:", e)


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


# ------------------ EMAIL READER ------------------ #

def read_emails():

    print("Checking unread emails...")

    creds = get_credentials()
    gmail_service = build('gmail', 'v1', credentials=creds)

    results = gmail_service.users().messages().list(
        userId='me',
        labelIds=['UNREAD'],
        maxResults=5
    ).execute()

    messages = results.get('messages', [])

    print("Unread found:", len(messages))

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

                print("\nEMAIL:\n", text)

                intent = extract_email_intent(text)
                print("AI OUTPUT:", json.dumps(intent, indent=2))

                process_intent(intent, text)


# ------------------ REMINDERS ------------------ #

def check_reminders():

    if not os.path.exists("events.json"):
        return

    with open("events.json", "r") as f:
        events = json.load(f)

    now = datetime.now(IST)
    updated = False

    for event in events:

        event_time = datetime.fromisoformat(event["datetime"])
        reminder_time = event_time - timedelta(hours=1)

        if not event["reminded"] and reminder_time <= now < event_time:

            print(f"\n🔔 Reminder: {event['title']}")

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


# ------------------ LOOP ------------------ #

def automation_loop():
    print("🤖 AgentX Running")
    print("Checking every 5 minutes...\n")

    while True:
        try:
            read_emails()
            check_reminders()
            print("Cycle done. Sleeping...\n")
            time.sleep(300)
        except Exception as e:
            print("Error:", e)
            time.sleep(60)


if __name__ == '__main__':
    automation_loop()