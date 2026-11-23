#!/bin/bash
# Hidden test (no arguments). Runs every method on disk -- every folder under checkpoints/
# holding unwrap.sh -- on the held-out meshes that only eval/test/ holds, scores the UV OBJs
# it writes, and writes the five scored numbers per method to scoring/scores_test.json
# (deleted first, written atomically at the end). See eval/test/run_hidden_test.py.
set -euo pipefail
cd /home/user
export TMPDIR="${TMPDIR:-/dev/shm}"
export PYTHONNOUSERSITE=1
exec python3 -u -m eval.test.run_hidden_test
