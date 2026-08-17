"""The gate proof.

A judge's requirement is that a fresh session recalls state written earlier.
Clearing a variable does not prove that. This test spawns genuinely separate
Python processes: one writes, the other reads, and they share nothing but
Sibyl Memory on disk.

This passing is the eligibility gate satisfied.
"""

import subprocess
import sys
import textwrap
import uuid

WRITER = """
from iterum.memory import write_counterparty, append_outcome_event
write_counterparty({name!r}, {{"outcomes": ["failed_after_payment"], "reputation": "untrusted"}})
append_outcome_event({name!r}, "failed_after_payment", {{"amount_usdc": "0.50"}})
print("written")
"""

READER = """
from iterum.memory import read_counterparty
body = read_counterparty({name!r})
assert body is not None, "cold session could not recall the counterparty"
assert body["reputation"] == "untrusted"
print("recalled", body["reputation"])
"""


def _run(source: str) -> str:
    result = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(source)],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def test_fresh_process_recalls_what_an_earlier_process_wrote():
    name = f"testvendor-{uuid.uuid4().hex[:8]}"

    assert _run(WRITER.format(name=name)) == "written"

    # Second process. No shared interpreter state, no shared client.
    assert "untrusted" in _run(READER.format(name=name))
