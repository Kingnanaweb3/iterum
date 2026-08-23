"""The counterparty graph.

Two layers, deliberately:

  journal   append-only outcome events, written via memory.append_outcome_event.
            This is the truth. Never rewritten, never deleted.

  entity    one consolidated record per counterparty, holding its outcome list.
            A cache of the journal. Rebuildable from it at any time.

Nothing here decides terms. That is terms.py. This module only records what
happened and reconstructs what is known.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from . import memory

# The outcomes Iterum can observe. Anything else is a bug, not a new outcome.
OUTCOMES = (
    "delivered",
    "late",
    "stale",
    "wrong_verdict",
    "failed_after_payment",
    "disputed_against",
)

NEGATIVE_OUTCOMES = ("stale", "wrong_verdict", "failed_after_payment", "disputed_against")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def record_transaction(
    name: str,
    outcome: str,
    *,
    amount_usdc: str | None = None,
    tx: str | None = None,
    note: str | None = None,
) -> None:
    """Record one transaction outcome.

    Writes to the journal first, then updates the consolidated entity. Journal
    first is deliberate: if the entity write fails, the truth still survives and
    rebuild_from_journal recovers it.
    """
    if outcome not in OUTCOMES:
        raise ValueError(f"unknown outcome {outcome!r}, expected one of {OUTCOMES}")

    detail: dict[str, Any] = {"ts": _now()}
    if amount_usdc is not None:
        detail["amount_usdc"] = amount_usdc
    if tx is not None:
        detail["tx"] = tx
    if note is not None:
        detail["note"] = note

    memory.append_outcome_event(name, outcome, detail)

    body = memory.read_counterparty(name) or {"outcomes": []}
    body["outcomes"] = body.get("outcomes", []) + [{"outcome": outcome, **detail}]
    body["last_seen"] = detail["ts"]
    memory.write_counterparty(name, body)


def get_history(name: str) -> list[dict[str, Any]]:
    """Every recorded outcome for one counterparty, oldest first.

    Read from the consolidated entity. This is the read on Iterum's decision
    path: a fresh process calls this before it transacts, and it returns events
    that process never witnessed.
    """
    body = memory.read_counterparty(name)
    if not body:
        return []
    return body.get("outcomes", [])


def rebuild_from_journal(name: str, *, limit: int = 500) -> list[dict[str, Any]]:
    """Reconstruct a counterparty's history from the journal alone.

    Proof that the entity is a cache and not the source of truth. Events cannot
    be filtered server-side by counterparty, so filter here.
    """
    events = memory.read_outcome_events(limit=limit)
    rebuilt = []
    for event in reversed(events):  # read_events returns newest first
        extra = event.get("extra") or {}
        if extra.get("counterparty") != name:
            continue
        rebuilt.append(
            {
                "outcome": extra.get("outcome"),
                "ts": extra.get("ts") or event.get("ts"),
                **{k: v for k, v in extra.items() if k not in ("counterparty", "outcome", "ts")},
            }
        )
    return rebuilt


def reconsolidate(name: str) -> list[dict[str, Any]]:
    """Rewrite a counterparty's entity from the journal. Repairs drift."""
    rebuilt = rebuild_from_journal(name)
    body = memory.read_counterparty(name) or {}
    body["outcomes"] = rebuilt
    if rebuilt:
        body["last_seen"] = rebuilt[-1]["ts"]
    memory.write_counterparty(name, body)
    return rebuilt


def known_counterparties() -> list[str]:
    return memory.list_counterparties()
