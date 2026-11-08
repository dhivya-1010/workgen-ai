"""Local institutional study platform services.

The platform deliberately uses durable JSON storage so it can run without
introducing a second database. Optional document parsers are used when
installed; unsupported binary formats fail explicitly instead of silently
creating empty knowledge.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from pypdf import PdfReader
from docx import Document

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "institutional_data"
DOCUMENT_DIR = DATA_DIR / "documents"
STATE_FILE = DATA_DIR / "state.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_state() -> dict[str, Any]:
    return {
        "institutions": [],
        "departments": [],
        "courses": [],
        "documents": [],
        "chunks": [],
        "answers": [],
        "submissions": [],
    }


def _load() -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DOCUMENT_DIR.mkdir(parents=True, exist_ok=True)
    if not STATE_FILE.exists():
        return _default_state()
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Institutional data is not valid JSON: {exc}") from exc
    base = _default_state()
    base.update(state)
    return base


def _save(state: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp = STATE_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(STATE_FILE)


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-zA-Z0-9]{3,}", text.lower())}


def _embedding(text: str, dimensions: int = 128) -> list[float]:
    """Create a small local embedding without requiring a hosted model."""
    vector = [0.0] * dimensions
    for token in _tokens(text):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        vector[index] += 1.0
    norm = sum(value * value for value in vector) ** 0.5 or 1.0
    return [round(value / norm, 6) for value in vector]


def _cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _extract_docx(path: Path) -> str:
    return "\n".join(paragraph.text for paragraph in Document(path).paragraphs if paragraph.text.strip())


def _extract_pptx(path: Path) -> str:
    values: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if name.startswith("ppt/slides/slide") and name.endswith(".xml"):
                root = ElementTree.fromstring(archive.read(name))
                values.extend(node.text for node in root.iter() if node.text and node.text.strip())
    return "\n".join(values)


def extract_text(path: Path, content: bytes) -> tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages).strip()
        if not text:
            try:
                import pytesseract
                from pdf2image import convert_from_bytes
                text = "\n".join(pytesseract.image_to_string(image) for image in convert_from_bytes(content)).strip()
            except ImportError:
                raise ValueError("This scanned PDF needs optional OCR dependencies: pytesseract and pdf2image.")
        return text, "pdf"
    if suffix == ".docx":
        return _extract_docx(path).strip(), "docx"
    if suffix == ".pptx":
        return _extract_pptx(path).strip(), "pptx"
    if suffix in {".txt", ".md", ".csv"}:
        return content.decode("utf-8", errors="replace").strip(), "text"
    raise ValueError("Supported formats are PDF, DOCX, PPTX, TXT, MD, and CSV.")


def _chunks(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    words = text.split()
    result = []
    for start in range(0, len(words), max(size - overlap, 1)):
        chunk = " ".join(words[start : start + size]).strip()
        if chunk:
            result.append(chunk)
    return result


def upload_document(
    filename: str,
    content: bytes,
    *,
    subject: str = "",
    unit: str = "",
    syllabus: str = "",
    academic_resource: str = "",
) -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DOCUMENT_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(filename).name
    document_id = str(uuid.uuid4())
    path = DOCUMENT_DIR / f"{document_id}-{safe_name}"
    path.write_bytes(content)
    try:
        text, file_type = extract_text(path, content)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    if not text:
        path.unlink(missing_ok=True)
        raise ValueError("No readable text was found in the document.")
    state = _load()
    document = {
        "id": document_id,
        "filename": safe_name,
        "file_type": file_type,
        "subject": subject.strip(),
        "unit": unit.strip(),
        "syllabus": syllabus.strip(),
        "academic_resource": academic_resource.strip(),
        "sha256": hashlib.sha256(content).hexdigest(),
        "text_length": len(text),
        "created_at": _now(),
    }
    state["documents"].append(document)
    for index, chunk in enumerate(_chunks(text)):
        state["chunks"].append({
            "id": str(uuid.uuid4()),
            "document_id": document_id,
            "index": index,
            "text": chunk,
            "terms": sorted(_tokens(chunk)),
            "embedding": _embedding(chunk),
        })
    _save(state)
    return document | {"chunk_count": sum(c["document_id"] == document_id for c in state["chunks"])}


def list_documents() -> list[dict[str, Any]]:
    return list(reversed(_load()["documents"]))


def delete_document(document_id: str) -> bool:
    state = _load()
    before = len(state["documents"])
    state["documents"] = [d for d in state["documents"] if d["id"] != document_id]
    state["chunks"] = [c for c in state["chunks"] if c["document_id"] != document_id]
    if len(state["documents"]) == before:
        return False
    for path in DOCUMENT_DIR.glob(f"{document_id}-*"):
        path.unlink(missing_ok=True)
    _save(state)
    return True


def search(query: str, *, subject: str = "", unit: str = "", limit: int = 8) -> list[dict[str, Any]]:
    state = _load()
    query_terms = _tokens(query)
    query_embedding = _embedding(query)
    documents = {d["id"]: d for d in state["documents"]}
    results = []
    for chunk in state["chunks"]:
        document = documents.get(chunk["document_id"])
        if not document:
            continue
        if subject and document["subject"].lower() != subject.lower():
            continue
        if unit and document["unit"].lower() != unit.lower():
            continue
        terms = set(chunk["terms"])
        lexical_score = len(query_terms & terms) / max(len(query_terms), 1)
        score = (0.65 * lexical_score) + (0.35 * _cosine(query_embedding, chunk.get("embedding", [])))
        if score > 0 or not query_terms:
            results.append({
                "score": round(score, 4),
                "text": chunk["text"],
                "source": {
                    "document_id": document["id"],
                    "filename": document["filename"],
                    "subject": document["subject"],
                    "unit": document["unit"],
                    "chunk": chunk["index"] + 1,
                },
            })
    return sorted(results, key=lambda item: item["score"], reverse=True)[:limit]


def create_answer(payload: dict[str, Any]) -> dict[str, Any]:
    question = payload.get("question", "").strip()
    if not question:
        raise ValueError("Question is required.")
    sources = search(question, subject=payload.get("subject", ""), unit=payload.get("unit", ""), limit=6)
    if not sources:
        raise ValueError("No matching institutional sources were found.")
    answer_text = " ".join(source["text"] for source in sources[:3])
    state = _load()
    answer = {
        "id": str(uuid.uuid4()),
        "question": question,
        "answer": answer_text,
        "subject": payload.get("subject", ""),
        "unit": payload.get("unit", ""),
        "marks": int(payload.get("marks") or 10),
        "status": "draft",
        "version": 1,
        "author": payload.get("author") or "AI draft",
        "sources": [source["source"] for source in sources],
        "created_at": _now(),
        "updated_at": _now(),
    }
    state["answers"].append(answer)
    _save(state)
    return answer


def list_answers(status: str = "") -> list[dict[str, Any]]:
    answers = list(reversed(_load()["answers"]))
    return [answer for answer in answers if not status or answer["status"] == status]


def update_answer(answer_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    state = _load()
    for answer in state["answers"]:
        if answer["id"] == answer_id:
            if "answer" in payload:
                answer["answer"] = str(payload["answer"]).strip()
            if "status" in payload:
                if payload["status"] not in {"draft", "approved", "published"}:
                    raise ValueError("Answer status must be draft, approved, or published.")
                answer["status"] = payload["status"]
            answer["version"] += 1
            answer["updated_at"] = _now()
            _save(state)
            return answer
    raise KeyError(answer_id)


def submit_answer(payload: dict[str, Any]) -> dict[str, Any]:
    answer_id = payload.get("answer_id")
    state = _load()
    approved = next((a for a in state["answers"] if a["id"] == answer_id and a["status"] in {"approved", "published"}), None)
    if not approved:
        raise ValueError("Students can submit only against an approved or published answer.")
    submission = {
        "id": str(uuid.uuid4()),
        "answer_id": answer_id,
        "student_answer": payload.get("student_answer", "").strip(),
        "created_at": _now(),
    }
    reference_terms = _tokens(approved["answer"])
    student_terms = _tokens(submission["student_answer"])
    missing = sorted(reference_terms - student_terms)
    submission["score"] = round(100 * len(reference_terms & student_terms) / max(len(reference_terms), 1))
    submission["missing_points"] = missing[:12]
    submission["feedback"] = "Strong coverage of the approved answer." if submission["score"] >= 75 else "Review the missing concepts and revisit the cited sources."
    state["submissions"].append(submission)
    _save(state)
    return submission


def dashboard() -> dict[str, Any]:
    state = _load()
    return {
        "documents": len(state["documents"]),
        "chunks": len(state["chunks"]),
        "draft_answers": sum(a["status"] == "draft" for a in state["answers"]),
        "approved_answers": sum(a["status"] in {"approved", "published"} for a in state["answers"]),
        "submissions": len(state["submissions"]),
        "institutions": state["institutions"],
        "departments": state["departments"],
        "courses": state["courses"],
    }
