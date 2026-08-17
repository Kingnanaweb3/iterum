# Iterum

An agent that pays other agents for services and remembers how each one behaved.

Every transaction closes with an outcome written to a counterparty graph in Sibyl Memory:
delivered, late, failed after payment, or disputed. The terms the agent offers next time are
derived from that history, not from configuration. A provider that took payment and returned
garbage gets prepayment refused, or gets skipped entirely.

Same counterparty, new session, different terms.

## What breaks when memory is deleted

Without memory the agent has no record of how any counterparty behaved, so every provider is a
stranger and it offers all of them identical terms forever. The product is terms that reflect
history, so deleting memory does not degrade Iterum, it removes the only input the decision has.

## Where memory is written and read

| What | File | Function |
| --- | --- | --- |
| Every Sibyl Memory call in the project | `src/iterum/memory.py` | `write_entity`, `read_entity`, `search_entities` |
| Outcome written after each transaction | `src/iterum/graph.py` | `record_outcome` |
| History read before each decision | `src/iterum/graph.py` | `get_history` |
| Terms derived from history | `src/iterum/terms.py` | `derive_terms` |
| Cold-session proof, two separate processes | `tests/test_cold_recall.py` | - |

`memory.py` is the only module that imports anything Sibyl. Everything else talks to Iterum's own
interface, so the storage layer can be swapped without touching the agent.

## How memory made this possible

Reputation is not a value you can compute from the transaction in front of you. It only exists in
the accumulation, and it only becomes useful in a session that did not witness the events that
formed it. Iterum's terms function reads a history it did not create, in a process that did not
observe any of it, which is the whole product. Sibyl Memory's graph model maps onto this directly:
providers are entities, transactions are typed edges, and the reputation state is consolidated
from outcome records rather than recomputed per call.

## Memory primitives used

- entities: providers as nodes in a counterparty graph
- recall: history read cold at the start of every decision
- consolidation: reputation state derived from raw outcome records
- temporal: reputation decays, so an old failure weighs less than a recent one

## Partner stacks

- **Base.** Payments settle via x402. The payment is the decision the memory governs, not an
  integration added alongside it. Network and chain ID: see `.env.example`.
- **Virtuals Protocol.** (Planned, conditional.) Provider agents registered so counterparties are
  real registered agents rather than local scripts.

## Prior work declaration

Iterum was scaffolded and prototyped before the Sep 1 build window opened. Work completed before
Sep 1 is listed below, with commit dates in the git history. Nothing in this repository is carried
over from an earlier project of mine or from a third-party codebase, beyond the dependencies listed
in `pyproject.toml`.

- Project scaffold and module layout
- Sibyl Memory adapter (`memory.py`), wired to MemoryClient, Aug 17
- Cold recall test passing against real Sibyl storage, Aug 17

## Running it

    pip install -e .
    cp .env.example .env
    pytest tests/
    python demo/run_demo.py

## Licence

MIT. See `LICENSE`.
