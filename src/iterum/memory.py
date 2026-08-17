"""The only module in Iterum that touches Sibyl Memory.

Two storage roles, deliberately separated:

  Events   (write_event / read_events)  the journal. One append-only record per
           transaction outcome. Never rewritten. This is the raw history.

  Entities (set_entity / get_entity)    the consolidated state. One record per
           counterparty holding its outcome list and derived reputation.
           Rewritten on every update.

The journal is the truth, the entity is the fast read. Iterum's decision path
reads the entity; the journal is what makes the entity reconstructable and gives
the temporal view.
"""

from __future__ import annotations

import os
from typing import Any

from sibyl_memory_client import MemoryClient

CATEGORY = "counterparty"

_DB_PATH = os.getenv("ITERUM_SIBYL_DB", "~/.sibyl-memory/memory.db")

_client: MemoryClient | None = None


def client() -> MemoryClient:
    """One client per process. A fresh process gets a fresh client and still sees
    everything an earlier process wrote, which is the point."""
    global _client
    if _client is None:
        _client = MemoryClient.local(_DB_PATH)
    return _client


# ---------------------------------------------------------------- entities

def write_counterparty(name: str, body: dict[str, Any]) -> dict[str, Any]:
    """Overwrite a counterparty's consolidated record."""
    return client().set_entity(CATEGORY, name, body)


def read_counterparty(name: str) -> dict[str, Any] | None:
    """Read a counterparty's consolidated record, or None if never seen."""
    try:
        record = client().get_entity(CATEGORY, name)
    except Exception:
        return None
    if not record:
        return None
    return record.get("body")


def list_counterparties() -> list[str]:
    return [e["name"] for e in client().list_entities(CATEGORY)]


# ---------------------------------------------------------------- events

def append_outcome_event(name: str, outcome: str, detail: dict[str, Any]) -> str:
    """Append one immutable outcome to the journal."""
    return client().write_event(
        acted=[f"transacted with {name}"],
        evaluated=[f"outcome: {outcome}"],
        extra={"counterparty": name, "outcome": outcome, **detail},
    )


def read_outcome_events(limit: int = 200) -> list[dict[str, Any]]:
    """Read the journal, newest first."""
    return client().read_events(limit=limit)


def forget_counterparty(name: str) -> None:
    """Remove a counterparty's consolidated record. Used to reset between demo
    takes. The journal is append-only and is not touched by this."""
    client().delete_entity(CATEGORY, name)
