#!/bin/bash
# Baseline check: the gym's xatlas outputs (checkpoints/xatlas_repro) registered alone and scored by the hidden test.
set -uo pipefail
NAME=baseline_xatlas
source /home/user/redteam/lib/env.sh
rm -rf "$ROOT"; mkdir -p "$ROOT/xatlas_repro"
for m in $RUN_MESHES; do ln -s "/home/user/checkpoints/xatlas_repro/$m" "$ROOT/xatlas_repro/$m"; done
bash "$RT/lib/hidden_test.sh" "$NAME" "$ROOT"
