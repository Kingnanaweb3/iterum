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
    none of these numbers can drift from what actually happened."""
    from .terms import DELTAS, NEGATIVE

    events = graph.memory.read_outcome_events(limit=5000)
    known = set(PROVIDERS)
    cheapest = min(PROVIDERS, key=lambda n: PROVIDERS[n]["price"])
    cheapest_price = PROVIDERS[cheapest]["price"]

    rows = []
    for e in reversed(events):  # oldest first
        extra = e.get("extra") or {}
        if extra.get("counterparty") in known and extra.get("outcome"):
            rows.append((extra["counterparty"], extra["outcome"], extra, e.get("ts")))

    transactions = len(rows)
    spent = wasted = 0.0
    overrides = 0
    by_outcome: dict[str, int] = {}
    per_seller: dict[str, dict[str, int]] = {n: {} for n in PROVIDERS}
    sessions = set()

    # tracked per seller as we walk the journal forward
    run = {n: 0 for n in PROVIDERS}
    best_run = {n: 0 for n in PROVIDERS}
    was_bad = {n: False for n in PROVIDERS}
    recoveries = {n: 0 for n in PROVIDERS}

    for seller, outcome, extra, ts in rows:
        by_outcome[outcome] = by_outcome.get(outcome, 0) + 1
        per_seller[seller][outcome] = per_seller[seller].get(outcome, 0) + 1
        if ts:
            sessions.add(ts[:13])  # hour buckets

        try:
            amount = float(extra.get("amount_usdc") or 0)
        except (TypeError, ValueError):
            amount = 0.0
        spent += amount
        if outcome in ("failed_after_payment", "wrong_verdict", "stale"):
            wasted += amount
        if seller != cheapest:
            overrides += 1

        if outcome == "delivered":
            run[seller] += 1
            best_run[seller] = max(best_run[seller], run[seller])
            # two clean deliveries after a bad record is a recovery
            if was_bad[seller] and run[seller] >= 2:
                recoveries[seller] += 1
                was_bad[seller] = False
        elif outcome in NEGATIVE:
            run[seller] = 0
            was_bad[seller] = True
        else:
            run[seller] = 0

    delivered = by_outcome.get("delivered", 0)
    lies = by_outcome.get("wrong_verdict", 0)
    failures = sum(by_outcome.get(o, 0) for o in NEGATIVE)

    # what the failures would have cost had the agent kept buying cheapest
    avoided = round(overrides * cheapest_price * (failures / transactions), 4) if transactions else 0.0

    movement = 0.0
    for outcome, count in by_outcome.items():
        movement += DELTAS.get(outcome, 0.0) * count

    assessment = assess_all()

    def pct(n):
        return round(100 * n / transactions, 1) if transactions else 0.0

    return {
        "transactions": transactions,
        "sessions": len(sessions),
        "delivered": delivered,
        "delivered_pct": pct(delivered),
        "failures": failures,
        "failure_pct": pct(failures),
        "lies": lies,
        "spent_usdc": round(spent, 4),
        "wasted_usdc": round(wasted, 4),
        "wasted_pct": round(100 * wasted / spent, 1) if spent else 0.0,
        "estimated_avoided_usdc": avoided,
        "overrides": overrides,
        "override_pct": pct(overrides),
        "recoveries": sum(recoveries.values()),
        "recoveries_per_seller": recoveries,
        "longest_clean_run": max(best_run.values()) if best_run else 0,
        "clean_runs_per_seller": best_run,
        "net_score_movement": round(movement, 1),
        "blocked": [n for n, t in assessment.items() if not t.selectable],
        "guarded": [n for n, t in assessment.items() if t.tier == "guarded"],
        "trusted": [n for n, t in assessment.items() if t.tier == "trusted"],
        "current_scores": {n: round(t.score, 1) for n, t in assessment.items()},
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
