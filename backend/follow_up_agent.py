"""Follow-Up Agent — AI-powered extraction of follow-ups from emails, meetings & knowledge."""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

FOLLOWUPS_FILE = Path(__file__).resolve().parent.parent / "followups.json"

# ---------------------------------------------------------------------------
# Mock AI extraction — simulates scanning real sources
# ---------------------------------------------------------------------------

MOCK_FOLLOWUPS = [
    {
        "source": "Email",
        "extracted_action": "Review Q3 budget proposal and approve resource allocation",
        "confidence": 92,
        "priority": "high",
        "due_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
        "context": "From: finance@company.com — Re: Q3 Budget Planning",
    },
    {
        "source": "Email",
        "extracted_action": "Send onboarding documents to new team member Sarah Chen",
        "confidence": 88,
        "priority": "high",
        "due_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "context": "From: hr@company.com — New hire starting Monday",
    },
    {
        "source": "Meeting",
        "extracted_action": "Draft architecture proposal for microservices migration",
        "confidence": 85,
        "priority": "medium",
        "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "context": 'Extracted from "Sprint Planning — Q3 Kickoff" — Alice assigned action item',
    },
    {
        "source": "Meeting",
        "extracted_action": "Schedule follow-up session with design team on UI refresh",
        "confidence": 76,
        "priority": "low",
        "due_date": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
        "context": 'Extracted from "Design Review — v2.5" — discussed in last 15 min',
    },
    {
        "source": "Meeting",
        "extracted_action": "Fix production login bug affecting SSO users",
        "confidence": 94,
        "priority": "high",
        "due_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
        "context": 'Extracted from "Incident Postmortem — 2025-04-10" — assigned to engineering',
    },
    {
        "source": "Knowledge",
        "extracted_action": "Update employee handbook with new remote work policy",
        "confidence": 73,
        "priority": "medium",
        "due_date": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"),
        "context": "Matched policy document: Remote_Work_Policy_v2.docx — pending review",
    },
    {
        "source": "Knowledge",
        "extracted_action": "Archive outdated compliance documents from shared drive",
        "confidence": 67,
        "priority": "low",
        "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "context": "7 documents flagged as expired by retention policy scanner",
    },
]

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_followups():
    """Load all follow-ups from the JSON file."""
    if not FOLLOWUPS_FILE.exists():
        return []
    try:
        with open(FOLLOWUPS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_followups(followups):
    """Persist the follow-up list to the JSON file."""
    with open(FOLLOWUPS_FILE, "w", encoding="utf-8") as f:
        json.dump(followups, f, indent=2)


def _next_id(followups: list) -> str:
    """Generate a simple unique id string."""
    if not followups:
        return "1"
    existing = set()
    for f in followups:
        try:
            existing.add(int(f["id"]))
        except (ValueError, KeyError):
            pass
    candidate = 1
    while candidate in existing:
        candidate += 1
    return str(candidate)


# ---------------------------------------------------------------------------
# AI Scan — simulate scanning sources for follow-ups
# ---------------------------------------------------------------------------

def scan_sources() -> dict:
    """Simulate AI scanning emails, meetings, and knowledge base for follow-ups.

    Returns a dict with scan metadata and the list of extracted follow-ups.
    Each follow-up has: source, extracted_action, confidence, priority, due_date, context.
    These are stored with status='pending' until the user accepts or dismisses them.
    """
    scan_id = datetime.now().strftime("scan_%Y%m%d_%H%M%S")

    # Jitter confidence slightly to feel more realistic
    extracted = []
    for item in MOCK_FOLLOWUPS:
        f = dict(item)
        f["confidence"] = max(10, min(99, f["confidence"] + random.randint(-5, 5)))
        extracted.append(f)

    # Shuffle to avoid predictable ordering
    random.shuffle(extracted)

    # Store them so GET /followups returns them
    existing = _load_followups()
    # Only keep previously accepted/dismissed items, replace pending
    kept = [f for f in existing if f.get("status") in ("accepted", "dismissed")]

    new_items = []
    for item in extracted:
        new_items.append({
            "id": _next_id(kept + new_items),
            "source": item["source"],
            "extracted_action": item["extracted_action"],
            "confidence": item["confidence"],
            "priority": item["priority"],
            "due_date": item.get("due_date", ""),
            "context": item.get("context", ""),
            "status": "pending",
            "scan_id": scan_id,
            "created_at": datetime.now().isoformat(),
            "resolved_at": None,
        })

    combined = kept + new_items
    _save_followups(combined)

    return {
        "scan_id": scan_id,
        "sources_scanned": [
            "Gmail (10 unread threads)",
            "Calendar (3 recent meetings)",
            "Knowledge Base (42 documents)",
        ],
        "total_extracted": len(new_items),
        "followups": new_items,
    }


# ---------------------------------------------------------------------------
# Public CRUD
# ---------------------------------------------------------------------------

def create_followup(title: str, source: str, due_date: str, priority: str) -> dict:
    """Create a new follow-up manually and persist it."""
    followups = _load_followups()
    followup = {
        "id": _next_id(followups),
        "title": title.strip(),
        "source": source,
        "due_date": due_date,
        "priority": priority,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
    }
    followups.append(followup)
    _save_followups(followups)
    return followup

def get_all_followups() -> list[dict]:
    """Return all follow-ups."""
    return _load_followups()


def get_followup_stats() -> dict:
    """Compute aggregate statistics for the UI."""
    followups = _load_followups()
    total = len(followups)
    pending = sum(1 for f in followups if f.get("status") == "pending")
    accepted = sum(1 for f in followups if f.get("status") == "accepted")
    dismissed = sum(1 for f in followups if f.get("status") == "dismissed")

    today = datetime.now().strftime("%Y-%m-%d")
    overdue = sum(
        1
        for f in followups
        if f.get("status") == "pending"
        and f.get("due_date", "")
        and f["due_date"] < today
    )

    return {
        "total": total,
        "pending": pending,
        "accepted": accepted,
        "dismissed": dismissed,
        "overdue": overdue,
    }


def update_followup(followup_id: str, data: dict) -> dict | None:
    """Update a follow-up's fields. Returns updated follow-up or None."""
    followups = _load_followups()
    for followup in followups:
        if followup["id"] == followup_id:
            if "status" in data:
                followup["status"] = data["status"]
                followup["resolved_at"] = (
                    datetime.now().isoformat()
                    if data["status"] in ("accepted", "dismissed")
                    else None
                )
            if "priority" in data:
                followup["priority"] = data["priority"]
            _save_followups(followups)
            return followup
    return None


def delete_followup(followup_id: str) -> bool:
    """Remove a follow-up by id. Returns True if deleted, False if not found."""
    followups = _load_followups()
    new_followups = [f for f in followups if f["id"] != followup_id]
    if len(new_followups) == len(followups):
        return False
    _save_followups(new_followups)
    return True
