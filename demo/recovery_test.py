"""The summary is a cache. The journal is the truth.

Corrupt a seller's consolidated record, then rebuild it from the journal and
show the terms come back identical. Nothing is backed up. It is recomputed.
"""
from iterum import graph, memory
from iterum.terms import derive_terms

NAME = "nadir"


def terms_line(label):
    t = derive_terms(graph.get_history(NAME))
    print(f"  {label:22} {t.tier:12} score {t.score:5.1f}  {t.payment_mode}")
    return t


def main():
    print(f"\nSummary and journal for {NAME}\n")
    before = terms_line("as recorded")
    journal = graph.rebuild_from_journal(NAME)
    print(f"  journal holds {len(journal)} events, entity holds {len(graph.get_history(NAME))}\n")

    print("Corrupting the summary...")
    memory.write_counterparty(NAME, {"outcomes": [], "last_seen": None})
    wiped = terms_line("summary destroyed")

    print("\nRebuilding from the journal...")
    graph.reconsolidate(NAME)
    after = terms_line("rebuilt")

    print()
    if (after.tier, after.score) == (before.tier, before.score):
        print("  Identical. The summary was never the truth.")
    else:
        print("  MISMATCH — the journal and the entity disagree.")
    print(f"  Wiped state would have bought at {wiped.tier}; recovered state is {after.tier}.\n")


if __name__ == "__main__":
    main()
