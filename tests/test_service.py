"""The callable API. Each key gets its own record, and nobody sees anyone else's."""
import pytest
from fastapi.testclient import TestClient

from iterum.api import app

client = TestClient(app)


def new_key():
    return client.post("/v1/keys").json()["key"]


def auth(key):
    return {"Authorization": f"Bearer {key}"}


def test_a_key_is_issued_without_signup():
    key = new_key()
    assert key.startswith("itr_")
    assert len(key) > 20


def test_two_keys_are_different():
    assert new_key() != new_key()


def test_no_key_is_rejected():
    assert client.get("/v1/terms/acme").status_code == 401


def test_a_malformed_header_is_rejected():
    r = client.get("/v1/terms/acme", headers={"Authorization": "itr_nope"})
    assert r.status_code == 401


def test_a_short_key_is_rejected():
    r = client.get("/v1/terms/acme", headers=auth("short"))
    assert r.status_code == 401


def test_an_unknown_counterparty_starts_provisional():
    r = client.get("/v1/terms/never-seen", headers=auth(new_key())).json()
    assert r["outcomes_recorded"] == 0
    assert r["terms"]["tier"] == "provisional"


def test_recording_changes_the_terms():
    key = new_key()
    r = client.post("/v1/record", headers=auth(key),
                    json={"counterparty": "acme", "outcome": "failed_after_payment"})
    assert r.status_code == 200
    assert r.json()["terms"]["tier"] == "guarded"
    assert r.json()["terms"]["payment_mode"] == "escrow"


def test_a_lie_blocks_a_counterparty():
    key = new_key()
    client.post("/v1/record", headers=auth(key),
                json={"counterparty": "liar", "outcome": "wrong_verdict"})
    terms = client.get("/v1/terms/liar", headers=auth(key)).json()["terms"]
    assert terms["tier"] == "blocked"
    assert terms["selectable"] is False


def test_an_invalid_outcome_is_refused():
    r = client.post("/v1/record", headers=auth(new_key()),
                    json={"counterparty": "acme", "outcome": "vibes"})
    assert r.status_code == 422


def test_one_caller_cannot_see_anothers_record():
    a, b = new_key(), new_key()
    client.post("/v1/record", headers=auth(a),
                json={"counterparty": "shared-name", "outcome": "wrong_verdict"})
    theirs = client.get("/v1/terms/shared-name", headers=auth(b)).json()
    assert theirs["outcomes_recorded"] == 0
    assert theirs["terms"]["tier"] == "provisional"


def test_the_same_key_sees_its_own_record_again():
    key = new_key()
    client.post("/v1/record", headers=auth(key),
                json={"counterparty": "acme", "outcome": "delivered"})
    assert client.get("/v1/terms/acme", headers=auth(key)).json()["outcomes_recorded"] == 1


def test_history_returns_both_layers():
    key = new_key()
    client.post("/v1/record", headers=auth(key),
                json={"counterparty": "acme", "outcome": "delivered"})
    r = client.get("/v1/history/acme", headers=auth(key)).json()
    assert len(r["entity"]) == 1
    assert len(r["journal"]) == 1


def test_the_outcome_vocabulary_is_public():
    outcomes = client.get("/v1/outcomes").json()["outcomes"]
    assert "wrong_verdict" in outcomes
    assert "delivered" in outcomes
