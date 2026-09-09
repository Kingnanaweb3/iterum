"""Turning a payment result into a recorded outcome.

This is where a provider's behaviour becomes a number. Getting it wrong means
punishing a slow seller as though it stole from you, or missing a lie.
"""
from datetime import datetime, timedelta, timezone

from iterum.agent import CONTROLS, _classify
from iterum.payments import PaymentResult

SAFE = "0x1111111111111111111111111111111111111111"
RISKY = "0x2222222222222222222222222222222222222222"


def ts(minutes_ago=0):
    t = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    return t.isoformat().replace("+00:00", "Z")


def body(address, verdict, minutes_ago=0):
    return {"address": address, "verdict": verdict, "as_of": ts(minutes_ago)}


def ok(address, verdict, minutes_ago=0, elapsed=1.0):
    return PaymentResult(True, True, 200, body(address, verdict, minutes_ago), elapsed)


def test_a_true_fresh_verdict_is_delivered():
    assert _classify("nadir", SAFE, ok(SAFE, "safe"))[0] == "delivered"


def test_a_true_verdict_on_a_risky_contract_is_delivered():
    assert _classify("nadir", RISKY, ok(RISKY, "risky"))[0] == "delivered"


def test_saying_safe_about_a_risky_contract_is_a_wrong_verdict():
    outcome, note = _classify("nadir", RISKY, ok(RISKY, "safe"))
    assert outcome == "wrong_verdict"
    assert "risky" in note


def test_saying_risky_about_a_safe_contract_is_also_wrong():
    assert _classify("nadir", SAFE, ok(SAFE, "risky"))[0] == "wrong_verdict"


def test_an_old_verdict_is_stale():
    outcome, note = _classify("nadir", SAFE, ok(SAFE, "safe", minutes_ago=90))
    assert outcome == "stale"
    assert "min old" in note


def test_staleness_is_checked_before_truth():
    # An old answer is reported as stale even when it happens to be correct.
    assert _classify("nadir", RISKY, ok(RISKY, "risky", minutes_ago=90))[0] == "stale"


def test_a_slow_but_correct_answer_is_late():
    assert _classify("nadir", SAFE, ok(SAFE, "safe", elapsed=99.0))[0] == "late"


def test_paid_but_nothing_returned_is_failed_after_payment():
    r = PaymentResult(False, True, 503, None, 0.4, "paid, provider returned 503")
    assert _classify("nadir", SAFE, r)[0] == "failed_after_payment"


def test_a_client_side_miss_is_not_the_sellers_fault():
    r = PaymentResult(False, False, 402, None, 0.9, "payment not attempted")
    assert _classify("nadir", SAFE, r)[0] == "payment_not_attempted"


def test_a_provider_that_never_answered_is_late_not_theft():
    r = PaymentResult(False, False, None, None, 99.0, "ReadTimeout")
    assert _classify("nadir", SAFE, r)[0] == "late"


def test_an_uncontrolled_address_cannot_be_graded_for_truth():
    unknown = "0x9999999999999999999999999999999999999999"
    assert unknown not in CONTROLS
    assert _classify("nadir", unknown, ok(unknown, "safe"))[0] == "delivered"


def test_a_missing_verdict_is_still_delivered_if_paid_and_fresh():
    r = PaymentResult(True, True, 200, {"as_of": ts()}, 1.0)
    assert _classify("nadir", SAFE, r)[0] == "delivered"


def test_controls_hold_both_kinds_of_truth():
    assert set(CONTROLS.values()) == {"safe", "risky"}
