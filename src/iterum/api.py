"""Read-only view of Iterum's memory, plus a rate-limited live run.

Judges can trigger one real screening from a funded throwaway wallet. The key
stays server side. Limits exist so the demo is still alive on judging day, not
for security: this is Base Sepolia and the USDC is worthless.
"""
from __future__ import annotations

import os
import time
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import graph
from .agent import CONTROLS, PROVIDERS, assess_all, screen
from .service import router as service_router

PER_IP_SECONDS = float(os.getenv("ITERUM_IP_COOLDOWN", 20))
TOTAL_RUNS = int(os.getenv("ITERUM_TOTAL_RUNS", 400))

_last: dict[str, float] = defaultdict(float)
_runs = {"n": 0}

app = FastAPI(title="Iterum")
app.include_router(service_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ITERUM_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


def _snapshot() -> dict:
    assessment = assess_all()
    sellers = []
    for name in PROVIDERS:
        t = assessment[name]
        history = graph.get_history(name)
        sellers.append({
            "name": name,
            "price": PROVIDERS[name]["price"],
            "tier": t.tier,
            "score": round(t.score, 1),
            "payment_mode": t.payment_mode,
            "cap": t.cap_usdc,
            "selectable": t.selectable,
            "reason": t.reason,
            "record": [h["outcome"] for h in history][-24:],
            "total": len(history),
        })
    return {"sellers": sellers, "runs_left": max(0, TOTAL_RUNS - _runs["n"])}


@app.get("/api/state")
def state():
    return _snapshot()


@app.get("/api/feed")
def feed(limit: int = 12):
    events = graph.memory.read_outcome_events(limit=limit)
    out = []
    for e in events:
        extra = e.get("extra") or {}
        if not extra.get("counterparty"):
            continue
        out.append({
            "ts": e.get("ts"),
            "seller": extra.get("counterparty"),
            "outcome": extra.get("outcome"),
            "note": extra.get("note"),
        })
    return {"events": out}


@app.post("/api/run")
async def run(request: Request):
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()

    if now - _last[ip] < PER_IP_SECONDS:
        wait = int(PER_IP_SECONDS - (now - _last[ip])) + 1
        return JSONResponse({"error": f"one run every {int(PER_IP_SECONDS)}s. try again in {wait}s"}, status_code=429)

    if _runs["n"] >= TOTAL_RUNS:
        return JSONResponse({"error": "the demo wallet is out of funds"}, status_code=429)

    _last[ip] = now
    _runs["n"] += 1

    import random
    address = random.choice(list(CONTROLS))
    result = await screen(address, verbose=False)

    return {"result": result, "state": _snapshot()}


@app.get("/api/stats")
def stats():
    """Counted from the journal, not stored. The journal is append-only, so
    these numbers cannot drift from what actually happened."""
    events = graph.memory.read_outcome_events(limit=2000)
    known = set(PROVIDERS)
    cheapest = min(PROVIDERS, key=lambda n: PROVIDERS[n]["price"])

    transactions = 0
    spent = 0.0
    overrides = 0
    by_outcome: dict[str, int] = {}

    for e in events:
        extra = e.get("extra") or {}
        seller = extra.get("counterparty")
        outcome = extra.get("outcome")
        if seller not in known or not outcome:
            continue
        transactions += 1
        by_outcome[outcome] = by_outcome.get(outcome, 0) + 1
        try:
            spent += float(extra.get("amount_usdc") or 0)
        except (TypeError, ValueError):
            pass
        # the record overrode price whenever the cheapest seller was not chosen
        if seller != cheapest:
            overrides += 1

    assessment = assess_all()
    blocked = [n for n, t in assessment.items() if not t.selectable]

    return {
        "transactions": transactions,
        "spent_usdc": round(spent, 4),
        "overrides": overrides,
        "override_pct": round(100 * overrides / transactions) if transactions else 0,
        "blocked": blocked,
        "by_outcome": dict(sorted(by_outcome.items(), key=lambda kv: -kv[1])),
    }
