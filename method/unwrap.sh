#!/bin/bash
# PartUV method entry point (the gym's method interface).
#   bash method/unwrap.sh <input_dir> <output_dir> [extra official_pipeline.py args]
# For every <name>.obj in <input_dir> writes <output_dir>/<name>/uv.obj.
# The hidden test calls checkpoints/<dir>/unwrap.sh, which forwards here for the reference.
set -euo pipefail
IN_DIR="$(cd "$1" && pwd)"
mkdir -p "$2"
OUT_DIR="$(cd "$2" && pwd)"
shift 2
export TMPDIR="${TMPDIR:-/dev/shm}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/dev/shm/matplotlib}"
export PYTHONFAULTHANDLER=1
export PYTHONNOUSERSITE=1
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export OPENBLAS_CORETYPE="${OPENBLAS_CORETYPE:-GENERIC}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"
export NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}"
cd /home/user
CKPT_PATH="${PARTFIELD_CHECKPOINT:-/home/user/data/downloads/partfield/model_objaverse.ckpt}"
if [ ! -f "$CKPT_PATH" ] && [ -f /home/user/checkpoints/partfield/model_objaverse.ckpt ]; then
  CKPT_PATH=/home/user/checkpoints/partfield/model_objaverse.ckpt
fi
test -f "$CKPT_PATH" || { echo "ERROR: PartField checkpoint missing. Run scripts/download.sh first."; exit 1; }
exec python3 -u -m method.official_pipeline \
  --data-dir "$IN_DIR" \
  --output-dir "$OUT_DIR" \
  --checkpoint-path "$CKPT_PATH" \
  --config-path /home/user/method/official_partuv/config/config.yaml \
  --threshold 1.25 \
  "$@"
