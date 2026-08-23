"""The ladder's behaviour, pinned.

These are the rows the demo depends on. If a delta or boundary changes and one
of these breaks, the demo beat changes too.
"""

from datetime import datetime, timedelta, timezone

import pytest

from iterum.terms import derive_terms, trust_score, clean_run

NOW = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)


def ago(days):
    return (NOW - timedelta(days=days)).isoformat().replace("+00:00", "Z")


def h(*pairs):
    return [{"outcome": o, "ts": ago(d)} for o, d in pairs]


def test_unknown_counterparty_starts_provisional():
    t = derive_terms([], now=NOW)
    assert t.tier == "provisional"
    assert t.payment_mode == "on_delivery"


def test_one_failure_drops_to_escrow_but_stays_selectable():
    t = derive_terms(h(("failed_after_payment", 0)), now=NOW)
    assert t.tier == "guarded"
    assert t.payment_mode == "escrow"
    assert t.selectable is True


def test_two_failures_blocks():
    t = derive_terms(h(("failed_after_payment", 1), ("failed_after_payment", 0)), now=NOW)
    assert t.tier == "blocked"
    assert t.payment_mode == "refuse"
    assert t.selectable is False


def test_sustained_delivery_earns_trusted():
    t = derive_terms(h(*[("delivered", d) for d in (3, 2, 1, 0)]), now=NOW)
    assert t.tier == "trusted"
    assert t.cap_usdc == 0.10


def test_old_failure_decays():
    fresh = trust_score(h(("failed_after_payment", 0)), now=NOW)
    old = trust_score(h(("failed_after_payment", 21)), now=NOW)
    assert old > fresh
    # 21 days is three half-lives, so roughly an eighth of the weight
    assert (60 - old) < (60 - fresh) / 4


def test_clean_run_resets_on_failure():
    assert clean_run(h(("delivered", 3), ("delivered", 2))) == 2
    assert clean_run(h(("delivered", 3), ("failed_after_payment", 2))) == 0
    assert clean_run(h(("failed_after_payment", 3), ("delivered", 2), ("delivered", 1))) == 2


def test_probation_holds_a_recovered_score_at_guarded():
    # Score alone would promote; the clean-run rule must hold it down.
    hist = h(("stale", 20), ("delivered", 0))
    t = derive_terms(hist, now=NOW)
    assert t.clean_run < 2
    assert t.tier == "guarded"


def test_terms_are_a_pure_function_of_history():
    hist = h(("delivered", 1))
    assert derive_terms(hist, now=NOW) == derive_terms(hist, now=NOW)


def test_unknown_outcome_contributes_nothing():
    assert trust_score([{"outcome": "invented", "ts": ago(0)}], now=NOW) == 60.0


def test_wrong_verdict_is_the_heaviest_penalty():
    from iterum.terms import DELTAS
    assert DELTAS["wrong_verdict"] < DELTAS["failed_after_payment"]
    assert DELTAS["wrong_verdict"] < DELTAS["stale"]


def test_one_wrong_verdict_blocks_immediately():
    # Lying about a contract is not a first-offence-forgiven event.
    t = derive_terms(h(("wrong_verdict", 0)), now=NOW)
    assert t.tier == "blocked"
    assert t.selectable is False


def test_wrong_verdict_counts_as_negative_for_probation():
    hist = h(("wrong_verdict", 20), ("delivered", 0))
    t = derive_terms(hist, now=NOW)
    assert t.clean_run == 1
    assert t.tier == "guarded"
