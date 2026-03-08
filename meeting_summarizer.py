import ollama
import json
import re

# ---------------- MEETING SUMMARIZER ---------------- #

def summarize_meeting(transcript):

    prompt = f"""
You are a meeting assistant.

Analyze the meeting transcript and produce structured output.

Return ONLY valid JSON in this format:

{{
  "summary": "short paragraph summary",
  "decisions": ["decision1", "decision2"],
  "actions": ["person - task"],
  "next_steps": ["step1", "step2"]
}}

Meeting Transcript:
{transcript}
"""

    try:
        response = ollama.chat(
            model="gemma:2b",
            messages=[{"role": "user", "content": prompt}]
        )

        raw_output = response["message"]["content"]

        # Try direct JSON parsing
        try:
            return json.loads(raw_output)

        except json.JSONDecodeError:
            # Extract JSON if model adds extra text
            match = re.search(r"\{[\s\S]*\}", raw_output)

            if match:
                return json.loads(match.group())

    except Exception as e:
        print("❌ Summarization error:", e)

    # fallback result
    return {
        "summary": "Could not generate summary",
        "decisions": [],
        "actions": [],
        "next_steps": []
    }