import os
from providers.common import build
app = build("nadir", "$0.005", os.environ["NADIR_PAY_TO"],
            {"dead": float(os.getenv("NADIR_DEAD_RATE", 0.25)),
             "wrong": float(os.getenv("NADIR_WRONG_RATE", 0.30)),
             "stale_minutes": 90})
