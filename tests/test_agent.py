"""Which seller gets chosen, given what the record says."""
import pytest

from iterum import agent, graph
from iterum.agent import PROVIDERS, assess_all, choose


@pytest.fixture
def no_exploring(monkeypatch):
    """choose() samples untried sellers at random. Turn that off so the
    price ordering is what is under test."""
    monkeypatch.setattr(agent, "EXPLORE_RATE", 0.0)


def record(name, outcome, times=1):
    for _ in range(times):
        graph.record_transaction(name, outcome)


def test_with_no_history_the_cheapest_is_chosen(no_exploring):
    assert choose(assess_all()) == "nadir"


def test_three_sellers_at_three_prices():
    prices = sorted(p["price"] for p in PROVIDERS.values())
    assert prices == [0.005, 0.02, 0.05]


def test_a_blocked_seller_is_skipped_however_cheap():
    record("nadir", "wrong_verdict")
    assert assess_all()["nadir"].selectable is False
    assert choose(assess_all()) != "nadir"


def test_the_next_cheapest_is_taken_when_the_cheapest_is_blocked(no_exploring):
    record("nadir", "wrong_verdict")
    assert choose(assess_all()) == "meridian"


def test_the_expensive_seller_is_the_last_resort(no_exploring):
    record("nadir", "wrong_verdict")
    record("meridian", "wrong_verdict")
    assert choose(assess_all()) == "aegis"


def test_nobody_is_chosen_when_everyone_is_blocked():
    for name in PROVIDERS:
        record(name, "wrong_verdict")
    assert choose(assess_all()) is None


def test_a_guarded_seller_is_still_selectable():
    record("nadir", "failed_after_payment")
    terms = assess_all()["nadir"]
    assert terms.tier == "guarded"
    assert terms.selectable is True


def test_every_seller_is_assessed_even_with_no_record():
    assessment = assess_all()
    assert set(assessment) == set(PROVIDERS)
    assert all(t.score == 60.0 for t in assessment.values())


def test_the_choice_reads_the_record_not_the_config():
    # Same code, same prices. Only the record differs.
    first = choose(assess_all())
    record("nadir", "wrong_verdict")
    assert choose(assess_all()) != first


def test_exploration_can_pick_an_untried_seller(monkeypatch):
    """Without this, a seller that is never chosen can never be known."""
    monkeypatch.setattr(agent, "EXPLORE_RATE", 1.0)
    record("nadir", "delivered")  # nadir is now the only tried seller
    picked = {choose(assess_all()) for _ in range(20)}
    assert picked - {"nadir"}, "exploration never sampled an untried seller"
