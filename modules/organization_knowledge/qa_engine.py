"""
Question Answering Engine — generates answers from retrieved document context.

Core principles:
  1. Prefer the provided document context.
  2. Combine information from multiple retrieved chunks when appropriate.
  3. Provide partial answers if only partial information exists.
  4. Only return NOT_FOUND_RESPONSE if there is absolutely no relevant information.
  5. Never invent company-specific facts or policies.

Supports two backends:
  - Google Gemini
  - OpenAI
"""

from __future__ import annotations

import logging
import re
from google import genai

from modules.organization_knowledge.config import (
    OrganizationKnowledgeSettings,
    get_settings,
)

logger = logging.getLogger("org_knowledge.qa_engine")


class QAEngineError(Exception):
    """Raised when the QA engine fails."""


SYSTEM_PROMPT = """
You are an Organization Knowledge Assistant.

Your primary source of truth is the retrieved organization documents.

Instructions:
1. Answer using the provided document context as much as possible.
2. If the answer can be reasonably inferred from the document, provide the inference.
3. Combine information from multiple document sections whenever needed.
4. If only partial information exists, answer with the available information instead of refusing.
5. Only say information is unavailable if the documents contain absolutely no relevant information.
6. Keep answers concise, natural, and helpful.
7. Never invent company-specific policies, dates, numbers, or facts that are not supported by the documents.
"""


NOT_FOUND_RESPONSE = (
    "I couldn't find any information about this in the uploaded organization documents."
)


def answer_question(
    question: str,
    context: str,
    settings: OrganizationKnowledgeSettings | None = None,
) -> dict:
    """
    Answer a question strictly using the retrieved context.
    """

    if settings is None:
        settings = get_settings()

    model_name = (
        settings.gemini_model
        if settings.llm_backend.lower() == "gemini"
        else settings.openai_llm_model
    )

    if not context or not context.strip():
        return {
            "answer": NOT_FOUND_RESPONSE,
            "source": "",
            "found": False,
            "model": model_name,
        }

    backend = settings.llm_backend.lower()

    user_prompt = f"""
Organization Documents:

{context}

User Question:
{question}

Answer the user's question using ONLY the organization documents above.

Guidelines:
- Prefer answering from the document.
- Combine information from multiple sections if required.
- If only partial information exists, answer with what is available.
- Only respond with "{NOT_FOUND_RESPONSE}" if absolutely no relevant information exists.
"""

    try:
        if backend == "gemini":
            result = _answer_with_gemini(user_prompt, settings)

        elif backend == "openai":
            result = _answer_with_openai(user_prompt, settings)

        else:
            result = _answer_with_extractive_fallback(question, context)

    except Exception as exc:
        logger.warning(
            "Primary LLM backend '%s' failed: %s. Falling back to extractive QA.",
            backend,
            exc,
        )

        result = _answer_with_extractive_fallback(question, context)

    answer_text = result.get("answer", "").strip()

    found = _is_answer_found(answer_text)

    if not found:
        answer_text = NOT_FOUND_RESPONSE

    result["answer"] = answer_text
    result["found"] = found
    result["source"] = context

    logger.info(
        "QA result: found=%s, model=%s, answer_len=%d",
        found,
        result.get("model"),
        len(answer_text),
    )

    return result


def _answer_with_openai(
    user_prompt: str,
    settings: OrganizationKnowledgeSettings,
) -> dict:

    try:
        from openai import OpenAI
    except ImportError:
        raise QAEngineError(
            "openai Python client is not installed. Run: pip install openai"
        )

    if not settings.openai_api_key:
        raise QAEngineError(
            "OpenAI API key is not set. Set the OPENAI_API_KEY environment variable."
        )

    client = OpenAI(api_key=settings.openai_api_key)

    model = settings.openai_llm_model

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=0,
        )

        answer = response.choices[0].message.content.strip()

        return {
            "answer": answer,
            "model": model,
        }

    except Exception as exc:
        raise QAEngineError(f"OpenAI chat failed: {exc}")


def _answer_with_gemini(
    user_prompt: str,
    settings: OrganizationKnowledgeSettings,
) -> dict:

    import os

    api_key = os.getenv("GEMINI_API_KEY") or settings.gemini_api_key

    if not api_key:
        raise QAEngineError("Gemini API key is not set.")

    client = genai.Client(api_key=api_key)

    model = os.getenv("GEMINI_MODEL", settings.gemini_model)

    try:
        response = client.models.generate_content(
            model=model,
            contents=f"{SYSTEM_PROMPT}\n\n{user_prompt}",
        )

        return {
            "answer": response.text.strip(),
            "model": model,
        }

    except Exception as exc:
        raise QAEngineError(f"Gemini failed: {exc}")


def _is_answer_found(answer_text: str) -> bool:
    """
    Returns True if the generated answer appears to contain
    useful information.
    """

    if not answer_text:
        return False

    lower = answer_text.lower()

    not_found_phrases = [
        "couldn't find any information",
        "information is unavailable",
        "no relevant information",
        "not available in the uploaded organization documents",
        "not available in the documents",
        "not mentioned in the documents",
    ]

    for phrase in not_found_phrases:
        if phrase in lower:
            return False

    return True


def _answer_with_extractive_fallback(
    question: str,
    context: str,
) -> dict:
    """
    Lightweight extractive QA fallback.
    """

    stop_words = {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "can",
        "could",
        "should",
        "would",
        "i",
        "you",
        "he",
        "she",
        "it",
        "we",
        "they",
        "on",
        "in",
        "at",
        "to",
        "for",
        "of",
        "with",
        "what",
        "where",
        "when",
        "how",
        "why",
        "do",
        "does",
        "did",
        "have",
        "has",
        "had",
        "be",
        "been",
        "being",
        "or",
        "and",
        "not",
    }

    raw_keywords = re.findall(r"\w+", question.lower())

    keywords = [
        word
        for word in raw_keywords
        if word not in stop_words and len(word) > 1
    ]

    if not keywords:
        return {
            "answer": NOT_FOUND_RESPONSE,
            "model": "extractive-fallback",
        }

    sentences = re.split(r"(?<=[.!?])\s+", context)

    scored_sentences = []

    for sentence in sentences:

        sentence = sentence.strip()

        if not sentence:
            continue

        score = sum(
            1 for keyword in keywords
            if keyword in sentence.lower()
        )

        if score:
            scored_sentences.append((score, sentence))

    if not scored_sentences:
        return {
            "answer": NOT_FOUND_RESPONSE,
            "model": "extractive-fallback",
        }

    scored_sentences.sort(reverse=True)

    best = [sentence for _, sentence in scored_sentences[:3]]

    answer = " ".join(best)

    return {
        "answer": answer,
        "model": "extractive-fallback",
    }