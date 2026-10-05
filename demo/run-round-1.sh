#!/usr/bin/env bash
# Swap in the round-1 implementation, run the v2 acceptance tests against it, restore.
# Use this at step 6 of the live build to show what the v1 criteria actually produced.
set -u
cd "$(dirname "$0")/.."
cp app/routes/summary.py /tmp/summary-round2.py
cp demo/round-1/summary.py app/routes/summary.py
echo "=== round-1 implementation, tested against the v2 acceptance criteria ==="
.venv/bin/python -m pytest tests/test_summary.py -q --no-header 2>&1 | tail -20
cp /tmp/summary-round2.py app/routes/summary.py
echo
echo "=== restored. round 2: ==="
.venv/bin/python -m pytest tests/test_summary.py -q --no-header 2>&1 | tail -3
