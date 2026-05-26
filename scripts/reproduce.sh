#!/bin/bash
set -euo pipefail
export TMPDIR=/dev/shm
export MPLCONFIGDIR=/dev/shm/matplotlib
export PYTHONFAULTHANDLER=1
export PYTHONNOUSERSITE=1
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export OPENBLAS_CORETYPE="${OPENBLAS_CORETYPE:-GENERIC}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"
export NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}"
cd /home/user

LIMIT="${PARTUV_LIMIT:-0}"

# Run baseline and PartUV on the same mesh subset.
bash scripts/baseline.sh /home/user/data/downloads/common_shapes /home/user/checkpoints/xatlas_repro "$LIMIT"
bash scripts/method.sh /home/user/data/downloads/common_shapes /home/user/checkpoints/partuv_repro "$LIMIT"

# Evaluate and produce scores
bash scripts/evaluate.sh compare \
  /home/user/checkpoints/xatlas_repro/results.json \
  /home/user/checkpoints/partuv_repro/results.json \
  /home/user/scoring/scores.json
