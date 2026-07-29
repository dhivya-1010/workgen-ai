"""Insight Agent — All insights derived from real AgentX data sources. ZERO mock data.

Data sources:
  - Email Intelligence:  followups.json (follow-ups extracted from emails)
  - Meeting Intelligence: knowledge_base.json (meeting summaries, actions, decisions)
  - Organizational Knowledge: ChromaDB via org-knowledge vector_store module
  - Analytics:  tasks.json (completion rates, stale tasks)
                 + followups.json (overdue/pending analytics)
                 + knowledge_base.json (meeting activity metrics)
"""
import json
import logging
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger("insight_agent")

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(relative_path: str) -> list[dict]:
    """Load a JSON list from project root. Returns [] on any failure."""
    fp = PROJECT_ROOT / relative_path
    if not fp.exists():
        return []
    try:
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not load %s: %s", relative_path, exc)
        return []


def _parse_dt(iso_str: str, fallback: datetime) -> datetime:
    """Parse ISO datetime, ensure timezone-aware."""
    if not iso_str:
        return fallback
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return fallback


def _priority_from_age(age_hours: float) -> str:
    """Derive priority based on age in hours."""
    if age_hours > 72:
        return "high"
    if age_hours > 24:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# 1. Email Intelligence — from followups.json
# ---------------------------------------------------------------------------

def _get_email_insights() -> list[dict[str, Any]]:
    """Insights derived from followups.json — real follow-ups from emails."""
    insights: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)
    followups = _load_json("followups.json")

    for fu in followups:
        title = fu.get("title", "Untitled")
        source = fu.get("source", "Email")
        priority = fu.get("priority", "medium")
        status = fu.get("status", "pending")
        due_date = fu.get("due_date", "")
        created_at = _parse_dt(fu.get("created_at", ""), now)

        if status != "pending":
            continue

        overdue = False
        if due_date:
            try:
                due_dt = datetime.strptime(due_date, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
                overdue = due_dt < now
            except (ValueError, TypeError):
                pass

        if overdue:
            insights.append({
                "title": f"Overdue Follow-up: {title}",
                "description": (
                    f"Follow-up from {source} was due {due_date}. "
                    f"Requires immediate attention."
                ),
                "source": "Email",
                "priority": "high",
                "detected_at": created_at.isoformat(),
                "icon": "⚠️",
            })
        else:
            age_hours = max(0.0, (now - created_at).total_seconds() / 3600)
            effective_priority = (
                _priority_from_age(age_hours) if priority == "medium" else priority
            )
            insights.append({
                "title": f"Pending Follow-up: {title}",
                "description": (
                    f"Follow-up from {source}. "
                    f"Created {int(age_hours)}h ago. "
                    f"Due: {due_date or 'Not set'}."
                ),
                "source": "Email",
                "priority": effective_priority,
                "detected_at": created_at.isoformat(),
                "icon": "📌",
            })

    return insights


# ---------------------------------------------------------------------------
# 2. Meeting Intelligence — from knowledge_base.json
# ---------------------------------------------------------------------------

def _get_meeting_insights() -> list[dict[str, Any]]:
    """Insights from knowledge_base.json meeting summaries."""
    insights: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)
    entries = _load_json("knowledge_base.json")

    for entry in entries:
        if entry.get("type") != "meeting":
            continue

        data = entry.get("data", {})
        title = data.get("title", "Untitled")
        summary = data.get("summary", "")
        actions = data.get("actions", [])
        decisions = data.get("decisions", [])
        next_steps = data.get("next_steps", [])
        date_iso = entry.get("date", "")
        meeting_date = _parse_dt(date_iso, now)
        age_days = (now - meeting_date).days
        summary_prefix = f"{summary[:200]}{'...' if len(summary) > 200 else ''}"

        if actions:
            items = "; ".join(actions[:3])
            if len(actions) > 3:
                items += f" (+{len(actions) - 3} more)"
            insights.append({
                "title": f"Meeting Actions: {title}",
                "description": f"{summary_prefix} Action items: {items}",
                "source": "Meeting",
                "priority": "high" if age_days < 2 else "medium",
                "detected_at": date_iso or now.isoformat(),
                "icon": "📋",
            })

        if decisions:
            items = "; ".join(decisions[:2])
            insights.append({
                "title": f"Meeting Decisions: {title}",
                "description": f"{summary_prefix} Decisions: {items}",
                "source": "Meeting",
                "priority": "medium",
                "detected_at": date_iso or now.isoformat(),
                "icon": "✅",
            })

        if next_steps:
            items = "; ".join(next_steps[:2])
            insights.append({
                "title": f"Meeting Next Steps: {title}",
                "description": f"Next steps: {items}",
                "source": "Meeting",
                "priority": "medium" if age_days < 7 else "low",
                "detected_at": date_iso or now.isoformat(),
                "icon": "➡️",
            })

    return insights


# ---------------------------------------------------------------------------
# 3. Organizational Knowledge — from ChromaDB
# ---------------------------------------------------------------------------

def _get_knowledge_insights() -> list[dict[str, Any]]:
    """Insights from Organization Knowledge ChromaDB vector store."""
    insights: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)

    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from modules.organization_knowledge.vector_store import (
            get_collection_count,
            get_stored_document_names,
        )
        from modules.organization_knowledge.config import get_settings

        settings = get_settings()
        doc_names = get_stored_document_names(settings)
        chunk_count = get_collection_count(settings)

        if doc_names and chunk_count > 0:
            insights.append({
                "title": f"Org Knowledge: {len(doc_names)} Document(s) Indexed",
                "description": (
                    f"{chunk_count} chunks indexed from: {', '.join(doc_names)}. "
                    f"Ready for policy and SOP queries."
                ),
                "source": "Knowledge",
                "priority": "low",
                "detected_at": now.isoformat(),
                "icon": "📚",
            })
            for doc in doc_names:
                insights.append({
                    "title": f"Document Available: {doc}",
                    "description": (
                        f"'{doc}' is indexed in the organization knowledge base."
                    ),
                    "source": "Knowledge",
                    "priority": "low",
                    "detected_at": now.isoformat(),
                    "icon": "📄",
                })
    except ImportError:
        logger.debug("Org knowledge module not available")
    except Exception as exc:
        logger.warning("Failed to query org knowledge: %s", exc)

    return insights


# ---------------------------------------------------------------------------
# 4. Analytics — computed from tasks.json, followups.json, knowledge_base.json
# ---------------------------------------------------------------------------

def _get_analytics_insights() -> list[dict[str, Any]]:
    """Analytics computed from real task / follow-up / meeting data."""
    insights: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)

    # --- Task analytics ---
    tasks = _load_json("tasks.json")
    total_tasks = len(tasks)
    done_tasks = sum(1 for t in tasks if t.get("done"))
    pending_tasks = total_tasks - done_tasks

    if total_tasks > 0:
        completion_rate = round((done_tasks / total_tasks) * 100, 1)
        insights.append({
            "title": f"Task Completion: {done_tasks}/{total_tasks} ({completion_rate}%)",
            "description": (
                f"{pending_tasks} pending, {done_tasks} completed. "
                f"{'On track!' if completion_rate > 50 else 'Focus on clearing pending tasks.'}"
            ),
            "source": "Analytics",
            "priority": "medium" if completion_rate < 50 else "low",
            "detected_at": now.isoformat(),
            "icon": "📊",
        })

        pending = [t for t in tasks if not t.get("done")]
        if pending:
            oldest = min(
                pending,
                key=lambda t: _parse_dt(t.get("created_at", ""), now),
            )
            oldest_created = _parse_dt(oldest.get("created_at", ""), now)
            age_hours = max(0.0, (now - oldest_created).total_seconds() / 3600)

            if age_hours > 1:
                insights.append({
                    "title": f"Stale Task: '{oldest.get('title', 'untitled')}'",
                    "description": (
                        f"Pending for {int(age_hours)}h ({age_hours/24:.1f}d). "
                        f"{'Consider breaking it down.' if age_hours > 72 else 'Review if still relevant.'}"
                    ),
                    "source": "Analytics",
                    "priority": _priority_from_age(age_hours),
                    "detected_at": oldest_created.isoformat(),
                    "icon": "⏰",
                })

    # --- Follow-up analytics ---
    followups = _load_json("followups.json")
    total_fu = len(followups)
    pending_fu = sum(1 for f in followups if f.get("status") == "pending")
    overdue_fu = 0
    for f in followups:
        due = f.get("due_date", "")
        if due and f.get("status") == "pending":
            try:
                due_dt = datetime.strptime(due, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
                if due_dt < now:
                    overdue_fu += 1
            except (ValueError, TypeError):
                pass

    if total_fu > 0:
        insights.append({
            "title": (
                f"Follow-ups: {pending_fu} Pending"
                f"{', ' + str(overdue_fu) + ' Overdue' if overdue_fu else ''}"
            ),
            "description": (
                f"{total_fu} total, {pending_fu} pending"
                f"{', ' + str(overdue_fu) + ' overdue' if overdue_fu else ''}. "
                f"{'Action needed!' if overdue_fu else 'All up to date.'}"
            ),
            "source": "Analytics",
            "priority": "high" if overdue_fu > 0 else "low",
            "detected_at": now.isoformat(),
            "icon": "📊",
        })

    # --- Meeting analytics ---
    meetings = _load_json("knowledge_base.json")
    meeting_count = sum(1 for e in meetings if e.get("type") == "meeting")
    if meeting_count > 0:
        total_actions = sum(
            len(e.get("data", {}).get("actions", []))
            for e in meetings if e.get("type") == "meeting"
        )
        insights.append({
            "title": f"Meeting Activity: {meeting_count} Meeting(s)",
            "description": (
                f"{meeting_count} meeting(s) analyzed with {total_actions} action item(s). "
                f"Review pending actions to stay on track."
            ),
            "source": "Analytics",
            "priority": "low",
            "detected_at": now.isoformat(),
            "icon": "📊",
        })

    return insights


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_all_insights() -> list[dict[str, Any]]:
    """Return all insights from real data sources. No mock data."""
    insights: list[dict[str, Any]] = []

    insights.extend(_get_email_insights())
    insights.extend(_get_meeting_insights())
    insights.extend(_get_knowledge_insights())
    insights.extend(_get_analytics_insights())

    # Sort: high priority first, then by detected_at descending
    priority_order = {"high": 0, "medium": 1, "low": 2}
    insights.sort(
        key=lambda x: (
            priority_order.get(x.get("priority", "low"), 2),
            x.get("detected_at", ""),
        )
    )

    return insights


def get_insight_stats() -> dict[str, int]:
    """Calculate summary statistics for the UI top cards."""
    insights = get_all_insights()
    total = len(insights)
    high_priority = sum(1 for i in insights if i.get("priority") == "high")
    action_required = sum(
        1 for i in insights if i.get("priority") in ("high", "medium")
    )
    informational = sum(1 for i in insights if i.get("priority") == "low")

    return {
        "total": total,
        "high_priority": high_priority,
        "action_required": action_required,
        "informational": informational,
    }
