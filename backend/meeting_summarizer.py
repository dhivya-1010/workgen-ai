from google import genai
import os
import json
import re
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY") or "placeholder_key"
)

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

    try:
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash"),
            contents=prompt
        )
        output = response.text or ""
    except Exception as exc:
        print(f"Meeting summarizer API error: {exc}")
        output = ""

    output = output.replace("```json", "").replace("```", "")

    match = re.search(r"\{[\s\S]*\}", output)

    if match:
        return json.loads(match.group())

    return {
        "title": "Meeting Summary",
        "summary": "Failed to summarize",
        "decisions": [],
        "actions": [],
        "next_steps": []
    }