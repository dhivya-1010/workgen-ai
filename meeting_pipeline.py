import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from meeting.meeting_summarizer import summarize_meeting
from meeting.notion_writer import write_summary

transcript = """
Alice: We need to finish the AgentX meeting summarizer.
Bob: I'll integrate the Notion API.
Charlie: I'll test the system tomorrow.
Alice: Let's present it Friday.
"""

summary = summarize_meeting(transcript)

print("SUMMARY:")
print(summary)

write_summary(summary)

print("Summary saved to Notion")