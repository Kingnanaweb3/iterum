#!/usr/bin/env bash
# Session two. A brand new process. Shares nothing with session one but memory.
set -a; source .env; set +a
source .venv/bin/activate
clear
echo "commit $(git rev-parse --short HEAD)   $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo
echo "--- what this new process can see ---"
python demo/run_demo.py 1 status
echo "--- what it does with that ---"
python demo/deletion_test.py
