"""Run the agent through a batch of screenings.

Nothing here is scripted. Which provider gets chosen depends on what memory
already holds, and whether a provider fails depends on its own failure profile.
The outcomes fall where they fall.

  python demo/run_demo.py            one batch of 8
  python demo/run_demo.py 20         one batch of 20
  python demo/run_demo.py 1 status   just show what memory currently holds
"""
import asyncio
import random
import sys

from iterum import graph
from iterum.agent import CONTROLS, PROVIDERS, assess_all, screen


def show_state(title: str) -> None:
    print(f"\n=== {title} ===")
    assessment = assess_all()
    for name in PROVIDERS:
        t = assessment[name]
        history = graph.get_history(name)
        counts: dict[str, int] = {}
        for entry in history:
            counts[entry["outcome"]] = counts.get(entry["outcome"], 0) + 1
        summary = ", ".join(f"{k} x{v}" for k, v in sorted(counts.items())) or "no history"
        print(f"  {name:9} {t.tier:12} score {t.score:5.1f}  {t.payment_mode:12} "
              f"cap {t.cap_usdc:<5}  [{summary}]")
    print()


async def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    status_only = len(sys.argv) > 2 and sys.argv[2] == "status"

    show_state("memory at start of session")
    if status_only:
        return

    addresses = list(CONTROLS)
    for i in range(1, n + 1):
        address = random.choice(addresses)
        print(f"[{i}/{n}] screening {address[:10]}...")
        await screen(address)

    show_state("memory at end of session")


if __name__ == "__main__":
    asyncio.run(main())
