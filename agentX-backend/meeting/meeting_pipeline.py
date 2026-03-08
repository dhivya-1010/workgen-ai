from meeting_summarizer import summarize_meeting
from notion_writer import write_summary

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