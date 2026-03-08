from __future__ import print_function
<<<<<<< HEAD

=======
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
from win10toast import ToastNotifier
from twilio.rest import Client

import os
import base64
import json
import ollama
import time
import re

from notion_client import Client as NotionClient
from dotenv import load_dotenv
<<<<<<< HEAD

=======
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
<<<<<<< HEAD

from datetime import datetime, timedelta, timezone

from meeting_summarizer import summarize_meeting
from knowledge_hub import store_meeting

=======
from datetime import datetime, timedelta, timezone

>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580

# ---------------- CONFIG ---------------- #

load_dotenv()

<<<<<<< HEAD
NOTION_MEETING_TOKEN = os.getenv("NOTION_MEETING_TOKEN")
=======
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
NOTION_DATABASE_ID = "31461e925a9480d29a9fefc14d9ac655"

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_TO = os.getenv("TWILIO_WHATSAPP_TO")

<<<<<<< HEAD
notion = NotionClient(auth=NOTION_MEETING_TOKEN) if NOTION_MEETING_TOKEN else None

IST = timezone(timedelta(hours=5, minutes=30))

toaster = ToastNotifier()

=======
notion = NotionClient(auth=NOTION_TOKEN) if NOTION_TOKEN else None

IST = timezone(timedelta(hours=5, minutes=30))
toaster = ToastNotifier()

# ✅ FIXED SCOPE
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar'
]


# ---------------- WHATSAPP ---------------- #

def send_whatsapp_message(text):

    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_WHATSAPP_TO:
        print("⚠ Twilio credentials missing")
        return

    try:
<<<<<<< HEAD

=======
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        message = client.messages.create(
            from_='whatsapp:+14155238886',
            body=text,
            to=TWILIO_WHATSAPP_TO
        )

        print("📲 WhatsApp sent:", message.sid)

    except Exception as e:
        print("WhatsApp Error:", e)


# ---------------- AUTH ---------------- #

def get_credentials():
<<<<<<< HEAD

=======
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
<<<<<<< HEAD

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:

            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)

=======
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
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


# ---------------- MARK EMAIL READ ---------------- #

def mark_email_read(gmail, message_id):
<<<<<<< HEAD

=======
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
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
<<<<<<< HEAD

=======
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
        if event.get('summary') == title:
            return True

    return False


<<<<<<< HEAD
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


# ---------------- NOTION ---------------- #

def add_to_notion(title, start_time):

    if not notion:
        return

    try:

        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Name": {"title": [{"text": {"content": title}}]},
                "Date": {"date": {"start": start_time.isoformat()}},
                "Status": {"select": {"name": "Pending"}},
                "Source": {"rich_text": [{"text": {"content": "Created by AgentX"}}]}
            }
        )

        print("📝 Added to Notion")

    except Exception as e:
        print("Notion Error:", e)


=======
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
# ---------------- CALENDAR ---------------- #

def create_calendar_event(title, start_time, intent_type, duration_minutes):

    creds = get_credentials()
<<<<<<< HEAD

    service = build('calendar', 'v3', credentials=creds)

    if event_exists(service, title, start_time):

=======
    service = build('calendar', 'v3', credentials=creds)

    if event_exists(service, title, start_time):
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
        print("⚠ Duplicate event skipped")
        return

    end_time = start_time + timedelta(minutes=duration_minutes)

    event = {
        'summary': title,
        'description': f"Created by AgentX ({intent_type})",
        'start': {'dateTime': start_time.isoformat(), 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end_time.isoformat(), 'timeZone': 'Asia/Kolkata'}
    }

    service.events().insert(calendarId='primary', body=event).execute()
<<<<<<< HEAD

    print("🎨 Added to Google Calendar")

    save_event_locally(title, start_time)

    add_to_notion(title, start_time)


=======
    print("🎨 Added to Google Calendar")

    save_event_locally(title, start_time)
    add_to_notion(title, start_time)


# ---------------- NOTION ---------------- #

def add_to_notion(title, start_time):

    if not notion:
        return

    try:
        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Name": {"title": [{"text": {"content": title}}]},
                "Date": {"date": {"start": start_time.isoformat()}},
                "Status": {"select": {"name": "Pending"}}
            }
        )
        print("📝 Added to Notion")
    except Exception as e:
        print("Notion Error:", e)


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


>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
# ---------------- EMAIL PROCESSOR ---------------- #

def process_email(original_text, gmail, message_id):

    text_lower = original_text.lower()
<<<<<<< HEAD

=======
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
    detected_type = classify_email_type(original_text)

    if "exam" in text_lower:
        detected_type = "exam"
<<<<<<< HEAD

=======
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
    elif "meeting" in text_lower:
        detected_type = "meeting"

    if detected_type == "none":
<<<<<<< HEAD

=======
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
        mark_email_read(gmail, message_id)
        return

    date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', original_text)
<<<<<<< HEAD

    if not date_match:

=======
    if not date_match:
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
        mark_email_read(gmail, message_id)
        return

    date_obj = datetime.strptime(date_match.group(1), "%d/%m/%Y")

    time_match = re.search(r'(\d{1,2}:\d{2}\s*(am|pm))', text_lower)
<<<<<<< HEAD

    if time_match:
        time_obj = datetime.strptime(time_match.group(1), "%I:%M %p").time()

=======
    if time_match:
        time_obj = datetime.strptime(time_match.group(1), "%I:%M %p").time()
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
    else:
        time_obj = datetime.strptime("09:00", "%H:%M").time()

    dt = datetime.combine(date_obj.date(), time_obj).replace(tzinfo=IST)

    duration_minutes = 60
<<<<<<< HEAD

    duration_match = re.search(r'(\d+(\.\d+)?)\s*hour', text_lower)

=======
    duration_match = re.search(r'(\d+(\.\d+)?)\s*hour', text_lower)
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
    if duration_match:
        duration_minutes = int(float(duration_match.group(1)) * 60)

    title = detected_type.capitalize()

    print(f"🔥 Detected {detected_type} → {title}")
<<<<<<< HEAD

    create_calendar_event(title, dt, detected_type, duration_minutes)

=======
    print(f"🕒 Scheduled at {dt.strftime('%Y-%m-%d %H:%M')}")

    create_calendar_event(title, dt, detected_type, duration_minutes)
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
    mark_email_read(gmail, message_id)


# ---------------- EMAIL READER ---------------- #

def read_emails():

    creds = get_credentials()
<<<<<<< HEAD

=======
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
    gmail = build('gmail', 'v1', credentials=creds)

    results = gmail.users().messages().list(
        userId='me',
        labelIds=['UNREAD'],
        maxResults=5
    ).execute()

    messages = results.get('messages', [])
<<<<<<< HEAD

=======
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
    print("Unread found:", len(messages))

    for msg in messages:

        msg_data = gmail.users().messages().get(
            userId='me',
            id=msg['id'],
            format='full'
        ).execute()

        parts = msg_data['payload'].get('parts', [])

        for part in parts:
<<<<<<< HEAD

=======
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
            if part['mimeType'] == 'text/plain':

                text = base64.urlsafe_b64decode(
                    part['body']['data']
                ).decode()

                print("\nEMAIL:\n", text)
<<<<<<< HEAD

=======
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
                process_email(text, gmail, msg['id'])


# ---------------- REMINDER ---------------- #

def check_reminders():

    if not os.path.exists("events.json"):
        return

    with open("events.json", "r") as f:
        events = json.load(f)

    now = datetime.now(IST)
<<<<<<< HEAD

=======
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
    updated = False

    for event in events:

        event_time = datetime.fromisoformat(event["datetime"])
<<<<<<< HEAD

=======
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
        reminder_time = event_time - timedelta(hours=1)

        if not event["reminded"] and reminder_time <= now < event_time:

            toaster.show_toast(
                "🔔 AgentX Reminder",
                f"{event['title']} at {event_time.strftime('%H:%M')}",
<<<<<<< HEAD
                duration=10,
                threaded=True
=======
                duration=10
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
            )

            whatsapp_text = (
                f"🔔 AgentX Reminder\n\n"
                f"{event['title']}\n"
                f"🕒 {event_time.strftime('%d %b %Y • %H:%M')}"
            )

            send_whatsapp_message(whatsapp_text)

            event["reminded"] = True
<<<<<<< HEAD

            updated = True

    if updated:

=======
            updated = True

    if updated:
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
        with open("events.json", "w") as f:
            json.dump(events, f, indent=2)


<<<<<<< HEAD
# ---------------- MEETING SUMMARIZER ---------------- #

def run_meeting_summarizer():

    print("\n===== AI Meeting Summarizer =====\n")

    transcript = input("Enter meeting transcript:\n")

    result = summarize_meeting(transcript)

    if not result:
        print("❌ Failed to summarize meeting.")
        return

    print("\n===== MEETING SUMMARY =====")

    print("\nSummary:")
    print(result.get("summary", ""))

    print("\nDecisions:")
    for d in result.get("decisions", []):
        print("-", d)

    print("\nAction Items:")
    for a in result.get("actions", []):
        print("-", a)

    print("\nNext Steps:")
    for s in result.get("next_steps", []):
        print("-", s)

    store_meeting(result)


# ---------------- LOOP ---------------- #

def automation_loop():

=======
# ---------------- LOOP ---------------- #

def automation_loop():
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
    print("🤖 AgentX Running")
    print("Checking every 5 minutes...\n")

    while True:
<<<<<<< HEAD

        try:

            read_emails()

            check_reminders()

            print("Cycle done. Sleeping...\n")

            time.sleep(300)

        except Exception as e:

            print("Error:", e)

            time.sleep(60)


# ---------------- MAIN ---------------- #

if __name__ == "__main__":

    print("""
AgentX System

1 → Run Email Automation
2 → Run Meeting Summarizer
""")

    choice = input("Select option: ")

    if choice == "1":

        automation_loop()

    elif choice == "2":

        run_meeting_summarizer()
=======
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
>>>>>>> 6ff4492cc7dec2543ea6bfbda37ac433cf8c4580
