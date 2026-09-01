"""x402 payment on Base. Thin wrapper so agent.py never touches the protocol.

Returns a PaymentResult that distinguishes three cases the agent must treat
differently:

  ok=True                 paid and got a body back
  paid=True, ok=False     money left, nothing usable came back
  paid=False, ok=False    payment never happened; our fault, not the provider's
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

from eth_account import Account
from x402 import x402Client
from x402.http.clients.httpx import x402HttpxClient
from x402.mechanisms.evm.exact import register_exact_evm_client
from x402.mechanisms.evm.signers import EthAccountSigner

NETWORK = os.getenv("X402_NETWORK", "eip155:84532")


@dataclass(frozen=True)
class PaymentResult:
    ok: bool
    paid: bool
    status: int | None
    body: dict[str, Any] | None
    elapsed: float
    error: str | None = None


def _client() -> x402Client:
    account = Account.from_key(os.environ["AGENT_PRIVATE_KEY"])
    return register_exact_evm_client(
        x402Client(), EthAccountSigner(account), networks=NETWORK
    )


async def buy(base_url: str, path: str, params: dict[str, Any], timeout: float = 10.0) -> PaymentResult:
    """Fetch a paid resource. Never raises; failures come back as a result."""
    t0 = time.perf_counter()
    try:
        async with x402HttpxClient(_client(), base_url=base_url, timeout=timeout) as http:
            r = await http.get(path, params=params)
            elapsed = time.perf_counter() - t0

            if r.status_code == 402:
                return PaymentResult(False, False, 402, None, elapsed,
                                     "payment not attempted")

            if r.status_code != 200:
                return PaymentResult(False, True, r.status_code, None, elapsed,
                                     f"paid, provider returned {r.status_code}")

            return PaymentResult(True, True, 200, r.json(), elapsed)

    except Exception as exc:
        elapsed = time.perf_counter() - t0
        name = type(exc).__name__
        # A timeout means the provider never answered. We cannot know whether
        # the authorization settled, so treat it as a slow provider rather than
        # accusing it of taking payment and absconding.
        timed_out = "Timeout" in name or elapsed >= timeout
        return PaymentResult(False, not timed_out, None, None, elapsed,
                             f"{name}: {exc}" if str(exc) else name)
