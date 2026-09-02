#!/usr/bin/env bash
# Session one. Memory starts empty. Let the outcomes fall where they fall.
set -a; source .env; set +a
source .venv/bin/activate
clear
echo "commit $(git rev-parse --short HEAD)   $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo
./reset-memory.sh
echo
python demo/run_demo.py 12
