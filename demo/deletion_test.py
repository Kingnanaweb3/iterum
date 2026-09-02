"""The gate, demonstrated rather than claimed.

Runs the same choice twice: once with memory, once with the memory read
stubbed out. With memory, the agent avoids what burned it. Without, every
seller is a stranger and it goes straight back to the cheapest one.
"""
import asyncio

from iterum import agent, graph
from iterum.agent import PROVIDERS, assess_all, choose


def show(label, assessment, pick):
    print(f"\n{label}")
    for name in PROVIDERS:
        t = assessment[name]
        print(f"  {name:9} {t.tier:12} score {t.score:5.1f}  {t.payment_mode}")
    print(f"  -> would buy from: {pick} at {PROVIDERS[pick]['price']} USDC" if pick
          else "  -> would buy from: nobody")


def main():
    with_memory = assess_all()
    show("WITH MEMORY", with_memory, choose(with_memory))

    # Delete the memory layer. Nothing else changes.
    original = graph.get_history
    graph.get_history = lambda name: []
    try:
        without = assess_all()
        show("MEMORY DELETED", without, choose(without))
    finally:
        graph.get_history = original

    print("\nSame code, same sellers, same prices. The only difference is the record.")


if __name__ == "__main__":
    main()
