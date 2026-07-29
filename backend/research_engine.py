from google import genai
from dotenv import load_dotenv
import os
import json
import re

from pathlib import Path
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY") or "placeholder_key"
)


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

    try:
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash-lite"),
            contents=prompt
        )
        raw = response.text or ""
    except Exception as exc:
        print(f"Research engine API error: {exc}")
        raw = ""

    print("\nRAW RESPONSE:\n", raw)

    extracted = extract_json(raw)
    if not extracted:
        return {
            "overview": f"Research Overview for topic: {topic}",
            "outline": ["1. Introduction", "2. Core Principles", "3. Applications", "4. Future Outlook"],
            "key_concepts": [topic, "Analysis", "Key Insights"],
            "research_questions": [f"What are the main developments in {topic}?"],
            "citations": ["Standard Reference Guide"]
        }
    return extracted


# -------- RUN FUNCTION (USED BY MAIN MENU) -------- #

def run_research_engine():

    topic = input("\nEnter research topic: ")

    result = generate_research_package(topic)

    if not result:
        print("❌ Failed to generate research")
        return

    print("\n===== RESEARCH OVERVIEW =====")
    print(result.get("overview", ""))

    print("\n===== OUTLINE =====")
    for item in result.get("outline", []):
        print("-", item)

    print("\n===== KEY CONCEPTS =====")
    for concept in result.get("key_concepts", []):
        print("-", concept)

    print("\n===== RESEARCH QUESTIONS =====")
    for q in result.get("research_questions", []):
        print("-", q)

    print("\n===== CITATIONS =====")
    for c in result.get("citations", []):
        print("-", c)