"""Single entrypoint for hosting.

Railway gives one port and one process, so the three sellers and the API are
mounted into one app. Locally you can still run them separately.
"""
import os

from fastapi import FastAPI

from .api import app as api
from providers.common import build

NET = os.getenv("X402_NETWORK", "eip155:84532")

app = FastAPI(title="Iterum")

app.mount("/p/aegis", build(
    "aegis", "$0.05", os.environ["AEGIS_PAY_TO"],
    {"dead": float(os.getenv("AEGIS_FAIL_RATE", 0.05))},
    mount="/p/aegis"))

app.mount("/p/meridian", build(
    "meridian", "$0.02", os.environ["MERIDIAN_PAY_TO"],
    {"timeout": float(os.getenv("MERIDIAN_TIMEOUT_RATE", 0.20)),
     "timeout_seconds": 9},
    mount="/p/meridian"))

app.mount("/p/nadir", build(
    "nadir", "$0.005", os.environ["NADIR_PAY_TO"],
    {"dead": float(os.getenv("NADIR_DEAD_RATE", 0.06)),
     "stale": float(os.getenv("NADIR_STALE_RATE", 0.10)),
     "wrong": float(os.getenv("NADIR_WRONG_RATE", 0.30)),
     "stale_minutes": 90},
    mount="/p/nadir"))

app.mount("/", api)
