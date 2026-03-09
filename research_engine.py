import ollama
import json
import re


def extract_json(text):
    try:
        return json.loads(text)
    except:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                return None
    return None


def generate_research_package(topic):

    prompt = f"""
You are an academic research assistant.

Generate research package for topic: "{topic}"

Return STRICT JSON:

{{
  "overview": "",
  "outline": [],
  "key_concepts": [],
  "research_questions": [],
  "citations": []
}}

Only JSON. No extra text.
"""

    response = ollama.chat(
        model="gemma:2b",
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.3}
    )

    raw = response["message"]["content"]

    print("\nRAW RESPONSE:\n", raw)

    return extract_json(raw)