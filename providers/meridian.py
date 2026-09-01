import os
from providers.common import build
app = build("meridian", "$0.02", os.environ["MERIDIAN_PAY_TO"],
            {"timeout": float(os.getenv("MERIDIAN_TIMEOUT_RATE", 0.35)),
             "timeout_seconds": 9})
