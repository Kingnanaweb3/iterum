"""The terms ladder.

History in, terms out. A pure function with no side effects and no I/O: every
value it returns is derived from recorded outcomes, and nothing here reads
configuration about a specific counterparty. That is what makes the deletion
test unambiguous. Remove the history and every counterparty gets identical
terms, because there is nothing else to go on.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any

BASELINE = 60.0
HALF_LIFE_DAYS = 7.0

DELTAS = {
    "delivered": 8.0,
    "late": 2.0,
    "stale": -20.0,
    "failed_after_payment": -35.0,
    "disputed_against": -15.0,
}

NEGATIVE = {"stale", "failed_after_payment", "disputed_against"}

# Promotion above a tier also requires this many consecutive clean deliveries
# since the last negative outcome. Score alone is not enough: one lucky call
# should not restore trust.
CLEAN_RUN_REQUIRED = 2


@dataclass(frozen=True)
class Terms:
    tier: str
    score: float
    payment_mode: str      # on_delivery | escrow | refuse
    cap_usdc: float
    retries: int
    selectable: bool
    clean_run: int
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _age_days(ts: str, now: datetime) -> float:
    return max(0.0, (now - _parse(ts)).total_seconds() / 86400.0)


def trust_score(history: list[dict[str, Any]], *, now: datetime | None = None) -> float:
    """Baseline plus age-weighted outcome deltas, clamped to 0..100.

    A seven-day half-life means a three-week-old failure carries about an eighth
    of the weight of a fresh one, so reputation recovers with time as well as
    with good behaviour.
    """
    now = now or datetime.now(timezone.utc)
    score = BASELINE
    for entry in history:
        delta = DELTAS.get(entry.get("outcome"), 0.0)
        ts = entry.get("ts")
        weight = 0.5 ** (_age_days(ts, now) / HALF_LIFE_DAYS) if ts else 1.0
        score += delta * weight
    return max(0.0, min(100.0, score))


def clean_run(history: list[dict[str, Any]]) -> int:
    """Consecutive 'delivered' outcomes since the most recent negative one."""
    count = 0
    for entry in reversed(history):
        outcome = entry.get("outcome")
        if outcome in NEGATIVE:
            break
        if outcome == "delivered":
            count += 1
        else:
            break  # 'late' interrupts a clean run without resetting trust
    return count


def _base_tier(score: float) -> str:
    if score >= 80:
        return "trusted"
    if score >= 60:
        return "provisional"
    if score >= 35:
        return "guarded"
    return "blocked"


def _has_negative(history: list[dict[str, Any]]) -> bool:
    return any(e.get("outcome") in NEGATIVE for e in history)


def derive_terms(history: list[dict[str, Any]], *, now: datetime | None = None) -> Terms:
    """The decision. Everything a caller needs to know about how to deal with
    this counterparty, derived entirely from what was recorded."""
    score = trust_score(history, now=now)
    run = clean_run(history)
    tier = _base_tier(score)
    reason = f"score {score:.1f} from {len(history)} recorded outcome(s)"

    # Probation: a counterparty that has ever failed cannot be promoted above
    # guarded until it has proven itself twice since that failure.
    if _has_negative(history) and run < CLEAN_RUN_REQUIRED and tier in ("trusted", "provisional"):
        tier = "guarded"
        reason += f"; held at guarded, {run}/{CLEAN_RUN_REQUIRED} clean deliveries since last failure"

    if tier == "trusted":
        return Terms(tier, score, "on_delivery", 0.10, 2, True, run, reason)
    if tier == "provisional":
        return Terms(tier, score, "on_delivery", 0.05, 1, True, run, reason)
    if tier == "guarded":
        return Terms(tier, score, "escrow", 0.02, 0, True, run, reason)
    return Terms(tier, score, "refuse", 0.0, 0, False, run, reason)
