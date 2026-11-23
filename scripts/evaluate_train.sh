#!/bin/bash
# Train-split evaluation (no arguments). Runs every method on disk -- every folder under
# checkpoints/ holding unwrap.sh -- on the visible training meshes, keeps its outputs in
# checkpoints/<dir>/train_outputs/, and writes scoring/scores_train.json.
# UV_TRAIN_REUSE=1 rescores existing train_outputs/ without running the method again.
set -euo pipefail
cd /home/user
export TMPDIR="${TMPDIR:-/dev/shm}"
export PYTHONNOUSERSITE=1
exec python3 -u -m eval.train.run_train_eval
