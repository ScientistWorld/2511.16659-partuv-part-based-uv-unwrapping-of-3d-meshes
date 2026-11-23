#!/bin/bash
# Usage: hidden_test.sh <scenario_name> <checkpoint_root>
#
# 1. Registers the scenario's outputs the way an agent does: bash scripts/evaluate_train.sh <root>
#    (this writes scoring/scores_train.json + scoring/scores_train_manifest.json).
# 2. Runs redteam/<name>/after_register.sh if present (what the agent leaves on disk afterwards).
# 3. Runs the hidden test exactly as the grader does: bash scripts/evaluate_test.sh (no arguments).
# 4. Copies scoring/scores_test.json (the only file the rank reads) into redteam/<name>/.
#
# Scenarios share scoring/, so this whole block is serialized with a file lock.
set -uo pipefail
NAME="$1"
CKPT_ROOT="$2"
cd /home/user
exec python3 - "$NAME" "$CKPT_ROOT" <<'PY'
import fcntl, subprocess, sys
name, root = sys.argv[1], sys.argv[2]
with open("/dev/shm/redteam_eval.lock", "w") as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    sys.exit(subprocess.call(["bash", "/home/user/redteam/lib/hidden_test_locked.sh", name, root]))
PY
