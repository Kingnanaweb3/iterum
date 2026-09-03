"""Iterum as a callable service.

Any agent can record what a counterparty did and ask what terms it has earned.
Each API key maps to a Sibyl Memory tenant, so one caller never sees another's
record.
"""
from __future__ import annotations

import hashlib
import os
import uuid
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from . import memory
from .graph import OUTCOMES, record_transaction, get_history, rebuild_from_journal
from .terms import derive_terms

router = APIRouter(prefix="/v1")

# key -> tenant uuid. Swap for a real store before this outlives the hackathon.
_KEYS: dict[str, str] = {}


def _tenant_for(key: str) -> str:
    """Deterministic tenant id from a key, so restarts do not orphan data."""
    if key not in _KEYS:
        digest = hashlib.sha256(key.encode()).hexdigest()[:32]
        _KEYS[key] = str(uuid.UUID(digest))
    return _KEYS[key]


def _scope(authorization: str | None) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "send: Authorization: Bearer <key>")
    key = authorization.removeprefix("Bearer ").strip()
    if len(key) < 12:
        raise HTTPException(401, "key too short")
    memory.client().set_tenant(_tenant_for(key))


class RecordIn(BaseModel):
    counterparty: str = Field(min_length=1, max_length=120)
    outcome: str
    amount_usdc: str | None = None
    note: str | None = None


@router.post("/keys")
def new_key() -> dict[str, str]:
    """Self-serve. No account, no email. Keep it, it is your namespace."""
    key = "itr_" + uuid.uuid4().hex
    _tenant_for(key)
    return {"key": key}


@router.post("/record")
def record(body: RecordIn, authorization: str | None = Header(None)) -> dict[str, Any]:
    _scope(authorization)
    if body.outcome not in OUTCOMES:
        raise HTTPException(422, f"outcome must be one of {list(OUTCOMES)}")
    record_transaction(
        body.counterparty, body.outcome,
        amount_usdc=body.amount_usdc, note=body.note,
    )
    t = derive_terms(get_history(body.counterparty))
    return {"counterparty": body.counterparty, "terms": t.as_dict()}


@router.get("/terms/{counterparty}")
def terms(counterparty: str, authorization: str | None = Header(None)) -> dict[str, Any]:
    _scope(authorization)
    history = get_history(counterparty)
    return {
        "counterparty": counterparty,
        "outcomes_recorded": len(history),
        "terms": derive_terms(history).as_dict(),
    }


@router.get("/history/{counterparty}")
def history(counterparty: str, authorization: str | None = Header(None)) -> dict[str, Any]:
    _scope(authorization)
    return {
        "counterparty": counterparty,
        "entity": get_history(counterparty),
        "journal": rebuild_from_journal(counterparty),
    }


@router.get("/outcomes")
def outcomes() -> dict[str, Any]:
    return {"outcomes": list(OUTCOMES)}
