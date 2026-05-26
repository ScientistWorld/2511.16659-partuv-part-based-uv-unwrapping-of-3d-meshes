#!/bin/bash
set -euo pipefail
export TMPDIR=/dev/shm
export PYTHONFAULTHANDLER=1
export PYTHONNOUSERSITE=1
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export OPENBLAS_CORETYPE="${OPENBLAS_CORETYPE:-GENERIC}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"
export NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}"
cd /home/user

CHECKPOINTS_ROOT="${CHECKPOINTS_ROOT:-/home/user/checkpoints}"

echo "=== ResearchGym split evaluation ==="
echo "Checkpoint root: $CHECKPOINTS_ROOT"
echo "Python: $(python3 --version)"

bash scripts/evaluate_train.sh "$CHECKPOINTS_ROOT" /home/user/scoring/scores_train.json
bash scripts/evaluate_test.sh "$CHECKPOINTS_ROOT" /home/user/scoring/scores_train.json /home/user/scoring/scores_test.json

test -f /home/user/scoring/scores_train.json
test -f /home/user/scoring/scores_test.json
python3 -m json.tool /home/user/scoring/scores_train.json >/dev/null
python3 -m json.tool /home/user/scoring/scores_test.json >/dev/null
