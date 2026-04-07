#!/bin/bash
set -e
export TMPDIR=/dev/shm
cd /home/user

LIMIT="${PARTUV_LIMIT:-0}"

bash scripts/download.sh
bash scripts/baseline.sh /home/user/data/common_shapes /home/user/checkpoints xatlas_repro "$LIMIT"
bash scripts/method.sh /home/user/data/common_shapes /home/user/checkpoints partuv_repro "$LIMIT"
bash scripts/evaluate.sh compare \
  /home/user/checkpoints/results_xatlas_repro.json \
  /home/user/checkpoints/results_partuv_repro.json \
  /home/user/scoring/scores.json
