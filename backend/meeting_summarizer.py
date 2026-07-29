import ollama
import json
import re

def summarize_meeting(transcript):

    prompt = f"""
You are a meeting assistant.

Generate a JSON object summarizing the meeting transcript below.
The "title" MUST be a concise, descriptive title summarizing the main topic or objective of the meeting (do NOT output "short meeting title" literally).

Return ONLY valid JSON with this exact schema:

{{
  "title": "<Concise descriptive title of the meeting>",
  "summary": "<Short executive summary>",
  "decisions": [],
  "actions": [],
  "next_steps": []
}}

Meeting Transcript:
{transcript}
"""

    response = ollama.chat(
        model="gemma:2b",
        messages=[{"role": "user", "content": prompt}]
    )

    output = response["message"]["content"]

    output = output.replace("```json","").replace("```","")

    match = re.search(r"\{[\s\S]*\}", output)

    if match:
        return json.loads(match.group())

    return {
        "summary": "Failed to summarize",
        "decisions": [],
        "actions": [],
        "next_steps": []
    }