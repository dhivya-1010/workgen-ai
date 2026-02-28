from __future__ import print_function
from win10toast import ToastNotifier

import os
import base64
import json
import ollama
import time
import re

from notion_client import Client
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from datetime import datetime, timedelta, timezone


# ---------------- CONFIG ---------------- #

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


# ---------------- AUTH ---------------- #

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


# ---------------- AI CLASSIFIER ---------------- #

def classify_email_type(email_text):

    prompt = f"""
Classify this email into ONE of:
meeting, exam, task, interview, payment, none.

Return ONLY JSON:
{{ "type": "" }}

Email:
{email_text}
"""

    response = ollama.chat(
        model="gemma:2b",
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0}
    )

    try:
        return json.loads(response["message"]["content"]).get("type", "none")
    except:
        return "none"


# ---------------- EMAIL PROCESSOR ---------------- #

def process_email(original_text, gmail, message_id):

    text_lower = original_text.lower()

    detected_type = classify_email_type(original_text)

    # Strong fallback detection
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
        mark_email_read(gmail, message_id)
        return

    # Date extraction
    date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', original_text)
    if not date_match:
        print("No date found.")
        mark_email_read(gmail, message_id)
        return

    try:
        date_obj = datetime.strptime(date_match.group(1), "%d/%m/%Y")
    except:
        print("Date parsing failed.")
        mark_email_read(gmail, message_id)
        return

    # Time extraction
    time_match = re.search(r'(\d{1,2}:\d{2}\s*(am|pm))', text_lower)
    if time_match:
        time_obj = datetime.strptime(time_match.group(1), "%I:%M %p").time()
    else:
        simple_time = re.search(r'(\d{1,2}\s*(am|pm))', text_lower)
        if simple_time:
            hour = int(simple_time.group(1).split()[0])
            ampm = simple_time.group(2)
            time_obj = datetime.strptime(f"{hour} {ampm}", "%I %p").time()
        else:
            time_obj = datetime.strptime("09:00", "%H:%M").time()

    dt = datetime.combine(date_obj.date(), time_obj).replace(tzinfo=IST)

    if dt < datetime.now(IST):
        print("Past date. Skipping.")
        mark_email_read(gmail, message_id)
        return

    # Duration
    duration_minutes = 60
    duration_match = re.search(r'(\d+(\.\d+)?)\s*hour', text_lower)
    if duration_match:
        duration_minutes = int(float(duration_match.group(1)) * 60)

    title = detected_type.capitalize()

    print(f"🔥 Detected {detected_type} → {title}")
    print(f"🕒 Scheduled at {dt.strftime('%Y-%m-%d %H:%M')}")

    create_calendar_event(title, dt, detected_type, duration_minutes)

    mark_email_read(gmail, message_id)


# ---------------- MARK EMAIL READ ---------------- #

def mark_email_read(gmail, message_id):
    gmail.users().messages().modify(
        userId='me',
        id=message_id,
        body={'removeLabelIds': ['UNREAD']}
    ).execute()


# ---------------- DUPLICATE CHECK ---------------- #

def event_exists(service, title, start_time):

    events = service.events().list(
        calendarId='primary',
        timeMin=start_time.isoformat(),
        timeMax=(start_time + timedelta(minutes=1)).isoformat(),
        singleEvents=True
    ).execute()

    for event in events.get('items', []):
        if event.get('summary') == title:
            return True

    return False


# ---------------- CALENDAR ---------------- #

def create_calendar_event(title, start_time, intent_type, duration_minutes):

    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)

    if event_exists(service, title, start_time):
        print("⚠ Duplicate event skipped")
        return

    end_time = start_time + timedelta(minutes=duration_minutes)

    color_map = {
        "meeting": "1",
        "task": "2",
        "exam": "11",
        "interview": "3",
        "payment": "6"
    }

    event = {
        'summary': title,
        'description': f"Created by AgentX ({intent_type})",
        'start': {'dateTime': start_time.isoformat(), 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end_time.isoformat(), 'timeZone': 'Asia/Kolkata'},
        'colorId': color_map.get(intent_type, "1")
    }

    service.events().insert(calendarId='primary', body=event).execute()
    print("🎨 Added to Google Calendar")

    save_event_locally(title, start_time)
    add_to_notion(title, start_time, intent_type)


# ---------------- NOTION ---------------- #

def add_to_notion(title, start_time, intent_type):

    if not notion:
        return

    try:
        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Name": {"title": [{"text": {"content": title}}]},
                "Date": {"date": {"start": start_time.isoformat()}},
                "Status": {"select": {"name": "Pending"}},
                "Source": {"rich_text": [{"text": {"content": f"Created by AgentX ({intent_type})"}}]}
            }
        )
        print("📝 Added to Notion")
    except:
        pass


# ---------------- LOCAL STORAGE ---------------- #

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


# ---------------- EMAIL READER ---------------- #

def read_emails():

    print("Checking unread emails...")

    creds = get_credentials()
    gmail = build('gmail', 'v1', credentials=creds)

    results = gmail.users().messages().list(
        userId='me',
        labelIds=['UNREAD'],
        maxResults=5
    ).execute()

    messages = results.get('messages', [])
    print("Unread found:", len(messages))

    for msg in messages:

        msg_data = gmail.users().messages().get(
            userId='me',
            id=msg['id'],
            format='full'
        ).execute()

        parts = msg_data['payload'].get('parts', [])

        for part in parts:
            if part['mimeType'] == 'text/plain':

                text = base64.urlsafe_b64decode(
                    part['body']['data']
                ).decode()

                print("\nEMAIL:\n", text)

                process_email(text, gmail, msg['id'])


# ---------------- REMINDER ---------------- #

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


# ---------------- LOOP ---------------- #

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