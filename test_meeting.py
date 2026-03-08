from meeting_summarizer import summarize_meeting

transcript = """
Alice: We need to finish the AgentX meeting summarizer this week.
Bob: I will handle the Notion API integration.
Charlie: I'll test the summarization pipeline tomorrow.
Alice: Let's demo it on Friday.
"""

result = summarize_meeting(transcript)

print(result)