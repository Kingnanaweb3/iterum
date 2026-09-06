"""The agent. Chooses a screener, pays it, judges what came back, remembers.

Every decision below is derived from recorded history via terms.derive_terms.
There is no per-provider configuration here beyond price and address.
Delete the memory and every provider is a stranger.
"""
from __future__ import annotations

import os
import random
from datetime import datetime, timedelta, timezone
from typing import Any

from . import graph
from .payments import buy
from .terms import derive_terms

CONTROLS = {
    "0x1111111111111111111111111111111111111111": "safe",
    "0x2222222222222222222222222222222222222222": "risky",
    "0x3333333333333333333333333333333333333333": "risky",
    "0x4444444444444444444444444444444444444444": "safe",
}

# Hosted: all three are mounted into one app, so they share a base URL.
# Local: each runs on its own port.
_BASE = os.getenv("ITERUM_PROVIDER_BASE")

PROVIDERS = {
    "aegis":    {"url": f"{_BASE}/p/aegis"    if _BASE else "http://localhost:8001", "price": 0.05},
    "meridian": {"url": f"{_BASE}/p/meridian" if _BASE else "http://localhost:8002", "price": 0.02},
    "nadir":    {"url": f"{_BASE}/p/nadir"    if _BASE else "http://localhost:8003", "price": 0.005},
}

FRESHNESS_MINUTES = 30
TIMEOUT_SECONDS = float(os.getenv("ITERUM_TIMEOUT", 6.0))


def assess_all() -> dict[str, Any]:
    """Current terms for every provider, read cold from memory."""
    return {name: derive_terms(graph.get_history(name)) for name in PROVIDERS}


EXPLORE_RATE = float(os.getenv("ITERUM_EXPLORE_RATE", 0.15))


def choose(assessment: dict[str, Any]) -> str | None:
    """Cheapest provider whose terms allow it and whose cap covers its price.

    With a small probability, sample an allowed provider the agent has never
    used instead. Without this, reputation is one-directional: a provider that
    is never chosen can never recover, and one never tried is never known.
    """
    candidates = [
        (PROVIDERS[n]["price"], n)
        for n, t in assessment.items()
        if t.selectable and PROVIDERS[n]["price"] <= t.cap_usdc
    ]
    if not candidates:
        return None

    untried = [n for _, n in candidates if not graph.get_history(n)]
    if untried and random.random() < EXPLORE_RATE:
        return random.choice(untried)

    return min(candidates)[1]


def _classify(name: str, address: str, result) -> tuple[str, str]:
    """Turn a payment result into a recorded outcome. Returns (outcome, note)."""
    if not result.paid:
        # Distinguish our client failing to pay from the provider stalling.
        if result.elapsed >= TIMEOUT_SECONDS:
            return "late", f"no response in {result.elapsed:.1f}s"
        return "payment_not_attempted", result.error or ""
    if not result.ok:
        return "failed_after_payment", result.error or ""

    body = result.body or {}
    verdict = body.get("verdict")
    as_of = body.get("as_of")

    if as_of:
        age = datetime.now(timezone.utc) - datetime.fromisoformat(as_of.replace("Z", "+00:00"))
        if age > timedelta(minutes=FRESHNESS_MINUTES):
            return "stale", f"as_of {int(age.total_seconds()/60)} min old"

    truth = CONTROLS.get(address.lower())
    if truth and verdict in ("safe", "risky") and verdict != truth:
        return "wrong_verdict", f"said {verdict}, truth is {truth}"

    if result.elapsed > TIMEOUT_SECONDS:
        return "late", f"{result.elapsed:.1f}s"

    return "delivered", ""


async def screen(address: str, *, verbose: bool = True) -> dict[str, Any]:
    """One screening. Reads memory, decides, pays, judges, writes back."""
    assessment = assess_all()
    name = choose(assessment)

    if name is None:
        if verbose:
            print("  no provider is selectable on current terms")
        return {"address": address, "provider": None, "outcome": None}

    terms = assessment[name]
    provider = PROVIDERS[name]

    if verbose:
        prices = ", ".join(
            f"{n} {PROVIDERS[n]['price']}"
            + ("" if assessment[n].selectable else " (blocked)")
            for n in sorted(PROVIDERS, key=lambda x: PROVIDERS[x]["price"])
        )
        print(f"  options:  {prices}")
        print(f"  picked:   {name} at {provider['price']} USDC")
        print(f"  because:  {terms.tier}, {terms.reason}")
        print(f"  will pay: {terms.payment_mode}, cap {terms.cap_usdc} USDC")

    result = await buy(provider["url"], "/screen", {"address": address},
                       timeout=TIMEOUT_SECONDS + 6)
    outcome, note = _classify(name, address, result)

    graph.record_transaction(
        name, outcome,
        amount_usdc=str(provider["price"]) if result.paid else None,
        note=note or None,
    )

    if verbose:
        verdict = (result.body or {}).get("verdict")
        if verdict:
            truth = CONTROLS.get(address.lower(), "unknown")
            print(f"  answer:   said '{verdict}', truth is '{truth}'")
        else:
            print(f"  answer:   none returned")
        detail = f" ({note})" if note else ""
        print(f"  RECORDED: {outcome}{detail}, {result.elapsed:.2f}s")
        print()

    return {"address": address, "provider": name, "outcome": outcome,
            "verdict": (result.body or {}).get("verdict")}
