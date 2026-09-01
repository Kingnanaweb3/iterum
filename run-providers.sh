#!/usr/bin/env bash
# Start the three screening providers. Ctrl-C stops all of them.
set -a; source .env; set +a
source .venv/bin/activate
uvicorn providers.aegis:app    --port 8001 &
uvicorn providers.meridian:app --port 8002 &
uvicorn providers.nadir:app    --port 8003 &
echo "aegis 8001 | meridian 8002 | nadir 8003"
trap 'kill 0' INT
wait
