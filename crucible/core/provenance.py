"""
Shared helpers for provenance tracking.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Mapping, Any


def _utc_now_iso() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(tz=timezone.utc).isoformat()


def build_provenance_entry(
    event_type: str,
    actor: str,
    *,
    source: str | None = None,
    description: str | None = None,
    reference_ids: Iterable[str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict:
    """
    Build a normalized provenance entry structure.

    Args:
        event_type: Machine-readable event type (design, eval_result, ranking, spec_update, etc.)
        actor: Which actor produced the event ("user", "agent", "system").
        source: Optional structured pointer (chat_session:..., run:..., ui_edit, etc.)
        description: Human readable summary.
        reference_ids: Optional list of IDs referenced by the event (run, candidate, evaluation ids, etc.)
        metadata: Optional structured metadata payload.

    Returns:
        dict with normalized provenance entry fields.
    """
    entry: dict[str, Any] = {
        "type": event_type,
        "timestamp": _utc_now_iso(),
        "actor": actor,
    }
    if source:
        entry["source"] = source
    if description:
        entry["description"] = description
    if reference_ids:
        entry["reference_ids"] = list(reference_ids)
    if metadata:
        entry["metadata"] = dict(metadata)
    return entry


def summarize_provenance_log(provenance_log: list[dict] | None) -> dict | None:
    """
    Generate a lightweight summary for UI/API listings.

    Args:
        provenance_log: The full provenance log list (may be None).

    Returns:
        dict with last event info and counts or None if no events exist.
    """
    if not provenance_log:
        return None

    last_event = provenance_log[-1]
    summary = {
        "event_count": len(provenance_log),
        "last_event": {
            "type": last_event.get("type"),
            "timestamp": last_event.get("timestamp"),
            "actor": last_event.get("actor"),
            "description": last_event.get("description"),
        },
    }

    if last_event.get("source"):
        summary["last_event"]["source"] = last_event["source"]
    return summary


