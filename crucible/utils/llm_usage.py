"""
Helpers for working with Kosmos LLM usage statistics.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional


def usage_stats_to_dict(response_or_usage: Any) -> Optional[Dict[str, Any]]:
    """
    Convert a Kosmos UsageStats or LLMResponse into a plain dict.

    Args:
        response_or_usage: Either an LLMResponse, UsageStats, or None.

    Returns:
        Dict with numeric token/cost info plus provider/model metadata, or None.
    """
    if response_or_usage is None:
        return None

    usage = getattr(response_or_usage, "usage", response_or_usage)
    if usage is None:
        return None

    data: Dict[str, Any] = {}

    for key in ("input_tokens", "output_tokens", "total_tokens"):
        value = getattr(usage, key, None)
        if value is not None:
            data[key] = int(value)

    cost = getattr(usage, "cost_usd", None)
    if cost is not None:
        data["cost_usd"] = float(cost)

    model = getattr(usage, "model", None) or getattr(response_or_usage, "model", None)
    if model:
        data["model"] = model

    provider = getattr(usage, "provider", None)
    if provider:
        data["provider"] = provider

    timestamp = getattr(usage, "timestamp", None)
    if isinstance(timestamp, datetime):
        data["timestamp"] = timestamp.isoformat()
    elif timestamp:
        data["timestamp"] = str(timestamp)

    return data or None


def aggregate_usage(usages: Iterable[Optional[Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
    """
    Aggregate multiple usage dicts into a single summary.

    Args:
        usages: Iterable of usage dicts (as produced by `usage_stats_to_dict`).

    Returns:
        Aggregated usage dict with totals, call_count, providers/models breakdown,
        or None if no usage data is provided.
    """
    entries: List[Dict[str, Any]] = [entry for entry in usages if entry]
    if not entries:
        return None

    aggregate: Dict[str, Any] = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "call_count": len(entries),
    }
    cost_total = 0.0
    cost_seen = False
    providers: Dict[str, int] = {}
    models: Dict[str, int] = {}

    for entry in entries:
        for key in ("input_tokens", "output_tokens", "total_tokens"):
            value = entry.get(key)
            if isinstance(value, (int, float)):
                aggregate[key] += int(value)

        cost = entry.get("cost_usd")
        if cost is not None:
            cost_seen = True
            cost_total += float(cost)

        provider = entry.get("provider")
        if provider:
            providers[provider] = providers.get(provider, 0) + 1

        model = entry.get("model")
        if model:
            models[model] = models.get(model, 0) + 1

    if cost_seen:
        aggregate["cost_usd"] = round(cost_total, 6)

    if providers:
        aggregate["providers"] = providers
    if models:
        aggregate["models"] = models

    return aggregate

