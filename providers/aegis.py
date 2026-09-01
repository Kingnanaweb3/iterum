import os
from providers.common import build
app = build("aegis", "$0.05", os.environ["AEGIS_PAY_TO"],
            {"dead": float(os.getenv("AEGIS_FAIL_RATE", 0.05))})
