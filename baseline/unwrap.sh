#!/bin/bash
# xatlas baseline entry point (same interface as method/unwrap.sh).
#   bash baseline/unwrap.sh <input_dir> <output_dir>
# For every <name>.obj in <input_dir> writes <output_dir>/<name>/uv.obj.
set -euo pipefail
IN_DIR="$(cd "$1" && pwd)"
mkdir -p "$2"
OUT_DIR="$(cd "$2" && pwd)"
export TMPDIR="${TMPDIR:-/dev/shm}"
export PYTHONNOUSERSITE=1
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"
cd /home/user
exec python3 -u -m baseline.export_xatlas_dataset --data-dir "$IN_DIR" --output-dir "$OUT_DIR"
