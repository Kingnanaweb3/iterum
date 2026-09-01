"""Shared x402 screening provider.

Each provider is the same server with a different name, price, receiving
address, and failure profile. Failure rates come from the environment so
rehearsal runs can be aggressive and the filmed run honest. The rates in use
are printed at startup and recorded in the README.
"""
import os, random, time
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from x402 import FacilitatorConfig, x402ResourceServer
from x402.http.facilitator_client import HTTPFacilitatorClient
from x402.http.middleware.fastapi import payment_middleware
from x402.mechanisms.evm.exact import register_exact_evm_server

NETWORK = os.getenv("X402_NETWORK", "eip155:84532")
FACILITATOR = os.getenv("FACILITATOR_URL", "https://x402.org/facilitator")

# Ground truth the agent also knows. Used to grade a verdict after the fact.
TRUTH = {
    "0x1111111111111111111111111111111111111111": "safe",
    "0x2222222222222222222222222222222222222222": "risky",
    "0x3333333333333333333333333333333333333333": "risky",
    "0x4444444444444444444444444444444444444444": "safe",
}


def _signals(verdict: str) -> dict:
    risky = verdict == "risky"
    return {
        "mint_authority_active": risky,
        "ownership_renounced": not risky,
        "lp_locked": not risky,
        "honeypot_pattern": risky,
    }


def build(name: str, price: str, pay_to: str, profile: dict) -> FastAPI:
    facilitator = HTTPFacilitatorClient(FacilitatorConfig(url=FACILITATOR))
    server = register_exact_evm_server(x402ResourceServer(facilitator), networks=NETWORK)

    routes = {
        "/screen": {
            "accepts": [
                {"scheme": "exact", "payTo": pay_to, "price": price, "network": NETWORK}
            ]
        }
    }

    app = FastAPI(title=name)
    app.middleware("http")(payment_middleware(routes, server))

    print(f"[{name}] price {price} payTo {pay_to} profile {profile}")

    @app.get("/screen")
    async def screen(address: str):
        roll = random.random()

        # Paid, then nothing usable. The worst-but-honest failure.
        if roll < profile.get("dead", 0.0):
            return JSONResponse({"error": "upstream unavailable"}, status_code=503)

        # Paid, then a slow response. The client may time out first.
        if roll < profile.get("dead", 0.0) + profile.get("timeout", 0.0):
            time.sleep(profile.get("timeout_seconds", 12))

        truth = TRUTH.get(address.lower(), "unknown")

        # Confidently wrong. This is the outcome the whole product exists for.
        if random.random() < profile.get("wrong", 0.0) and truth != "unknown":
            verdict = "safe" if truth == "risky" else "risky"
        else:
            verdict = truth

        age = profile.get("stale_minutes", 0)
        as_of = datetime.now(timezone.utc) - timedelta(minutes=age)

        return {
            "address": address,
            "verdict": verdict,
            "signals": _signals(verdict),
            "as_of": as_of.isoformat().replace("+00:00", "Z"),
            "provider": name,
        }

    return app
