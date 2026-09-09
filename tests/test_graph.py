"""The two storage layers: the journal that is never edited, and the summary
that is rebuilt from it."""
import pytest

from iterum import graph, memory


def test_unknown_outcome_is_rejected():
    with pytest.raises(ValueError):
        graph.record_transaction("acme", "went_badly")


def test_every_declared_outcome_is_accepted():
    for outcome in graph.OUTCOMES:
        graph.record_transaction("acme", outcome)
    assert len(graph.get_history("acme")) == len(graph.OUTCOMES)


def test_history_is_oldest_first():
    graph.record_transaction("acme", "delivered")
    graph.record_transaction("acme", "stale")
    graph.record_transaction("acme", "wrong_verdict")
    assert [h["outcome"] for h in graph.get_history("acme")] == [
        "delivered", "stale", "wrong_verdict",
    ]


def test_unknown_counterparty_has_no_history():
    assert graph.get_history("never-seen") == []


def test_amount_and_note_are_kept():
    graph.record_transaction("acme", "delivered", amount_usdc="0.005", note="fine")
    entry = graph.get_history("acme")[-1]
    assert entry["amount_usdc"] == "0.005"
    assert entry["note"] == "fine"


def test_journal_matches_the_summary():
    for outcome in ("delivered", "late", "wrong_verdict"):
        graph.record_transaction("acme", outcome)
    assert [h["outcome"] for h in graph.rebuild_from_journal("acme")] == \
           [h["outcome"] for h in graph.get_history("acme")]


def test_journal_ignores_other_counterparties():
    graph.record_transaction("acme", "delivered")
    graph.record_transaction("other", "stale")
    rebuilt = graph.rebuild_from_journal("acme")
    assert len(rebuilt) == 1
    assert rebuilt[0]["outcome"] == "delivered"


def test_destroyed_summary_rebuilds_exactly():
    for outcome in ("delivered", "failed_after_payment", "delivered"):
        graph.record_transaction("acme", outcome)
    before = [h["outcome"] for h in graph.get_history("acme")]

    memory.write_counterparty("acme", {"outcomes": [], "last_seen": None})
    assert graph.get_history("acme") == []

    graph.reconsolidate("acme")
    assert [h["outcome"] for h in graph.get_history("acme")] == before


def test_the_journal_survives_a_destroyed_summary():
    graph.record_transaction("acme", "wrong_verdict")
    memory.write_counterparty("acme", {"outcomes": []})
    assert len(graph.rebuild_from_journal("acme")) == 1


def test_forgetting_a_counterparty_leaves_the_journal_intact():
    graph.record_transaction("acme", "delivered")
    memory.forget_counterparty("acme")
    assert graph.get_history("acme") == []
    assert len(graph.rebuild_from_journal("acme")) == 1


def test_known_counterparties_lists_what_was_recorded():
    graph.record_transaction("one", "delivered")
    graph.record_transaction("two", "delivered")
    assert set(graph.known_counterparties()) == {"one", "two"}


def test_negative_outcomes_are_declared():
    assert set(graph.NEGATIVE_OUTCOMES) <= set(graph.OUTCOMES)
    assert "wrong_verdict" in graph.NEGATIVE_OUTCOMES
    assert "delivered" not in graph.NEGATIVE_OUTCOMES
