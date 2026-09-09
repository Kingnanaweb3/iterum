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
    """Counted from the journal, not stored anywhere. The journal is
    append-only, so these numbers cannot drift from what happened."""
    events = graph.memory.read_outcome_events(limit=5000)
    known = set(PROVIDERS)
    cheapest = min(PROVIDERS, key=lambda n: PROVIDERS[n]["price"])

    transactions = 0
    spent = 0.0
    overrides = 0
    paid_for_nothing = 0.0
    by_outcome: dict[str, int] = {}
    per_seller: dict[str, dict[str, int]] = {n: {} for n in PROVIDERS}

    for e in events:
        extra = e.get("extra") or {}
        seller, outcome = extra.get("counterparty"), extra.get("outcome")
        if seller not in known or not outcome:
            continue

        transactions += 1
        by_outcome[outcome] = by_outcome.get(outcome, 0) + 1
        per_seller[seller][outcome] = per_seller[seller].get(outcome, 0) + 1

        try:
            amount = float(extra.get("amount_usdc") or 0)
        except (TypeError, ValueError):
            amount = 0.0
        spent += amount

        # money that bought nothing usable
        if outcome in ("failed_after_payment", "wrong_verdict", "stale"):
            paid_for_nothing += amount

        # the record overrode price whenever the cheapest seller was not used
        if seller != cheapest:
            overrides += 1

    delivered = by_outcome.get("delivered", 0)
    lies = by_outcome.get("wrong_verdict", 0)
    failures = sum(by_outcome.get(o, 0) for o in
                   ("failed_after_payment", "wrong_verdict", "stale", "disputed_against"))

    assessment = assess_all()
    blocked = [n for n, t in assessment.items() if not t.selectable]
    guarded = [n for n, t in assessment.items() if t.tier == "guarded"]

    def pct(n):
        return round(100 * n / transactions, 1) if transactions else 0.0

    return {
        "transactions": transactions,
        "delivered": delivered,
        "delivered_pct": pct(delivered),
        "failures": failures,
        "failure_pct": pct(failures),
        "lies": lies,
        "spent_usdc": round(spent, 4),
        "wasted_usdc": round(paid_for_nothing, 4),
        "overrides": overrides,
        "override_pct": pct(overrides),
        "blocked": blocked,
        "guarded": guarded,
        "by_outcome": dict(sorted(by_outcome.items(), key=lambda kv: -kv[1])),
        "per_seller": per_seller,
    }


@app.get("/api/integrity")
def integrity():
    """For every seller, does the summary still match the journal?

    Reported rather than asserted: the summary is a cache, and this is the
    check that says whether it needs rebuilding."""
    report = []
    for name in PROVIDERS:
        entity = [h.get("outcome") for h in graph.get_history(name)]
        journal = [h.get("outcome") for h in graph.rebuild_from_journal(name)]
        report.append({
            "seller": name,
            "summary_entries": len(entity),
            "journal_entries": len(journal),
            "in_sync": entity == journal,
        })
    return {
        "sellers": report,
        "all_in_sync": all(r["in_sync"] for r in report),
    }
