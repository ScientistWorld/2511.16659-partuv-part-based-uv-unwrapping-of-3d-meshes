#!/bin/bash
set -e
export TMPDIR=/dev/shm
export MPLCONFIGDIR=/dev/shm/matplotlib
export PYTHONPATH=/home/user/.local/lib/python3.12/site-packages
cd /home/user

LIMIT="${PARTUV_LIMIT:-0}"

# Run PartUV method on meshes
bash scripts/method.sh /home/user/data/common_shapes /home/user/checkpoints/partuv_repro "$LIMIT"

# Evaluate and produce scores
bash scripts/evaluate.sh compare \
  /home/user/checkpoints/xatlas_repro/results.json \
  /home/user/checkpoints/partuv_repro/results.json \
  /home/user/scoring/scores.json