#!/bin/bash
set -euo pipefail
export TMPDIR=/dev/shm
export MPLCONFIGDIR=/dev/shm/matplotlib
cd /home/user

# Submission smoke: run one mesh through baseline, method, and evaluation.
# Full reproduction remains: PARTUV_LIMIT=0 bash scripts/reproduce.sh
LIMIT="${PARTUV_LIMIT:-1}"
SMOKE_ROOT="${PARTUV_SMOKE_ROOT:-/home/user/checkpoints/smoke}"

echo "=== PartUV reproduction run ==="
echo "Mesh limit: ${LIMIT:-all}"
echo "Python: $(python3 --version)"
python3 - <<'PY' || true
try:
    import torch
    print(f"Torch: {torch.__version__}; CUDA available: {torch.cuda.is_available()}", flush=True)
except Exception as exc:
    print(f"Torch import failed: {type(exc).__name__}: {exc}", flush=True)
PY

# Verify resources exist (these are bind-mounted from workspace at runtime)
test -f /home/user/checkpoints/partfield/model_objaverse.ckpt || { echo "ERROR: PartField checkpoint missing at /home/user/checkpoints/partfield/model_objaverse.ckpt"; exit 1; }
test -d /home/user/data/common_shapes || { echo "ERROR: Common Shapes dataset missing at /home/user/data/common_shapes"; exit 1; }
echo "Dataset meshes: $(find /home/user/data/common_shapes -maxdepth 1 -name '*.obj' | wc -l)"
echo "Checkpoint bytes: $(stat -c '%s' /home/user/checkpoints/partfield/model_objaverse.ckpt)"

# Run end-to-end on isolated smoke outputs so the canonical 24-mesh scores
# in scoring/scores.json remain the full reproduction artifact.
rm -rf "$SMOKE_ROOT"
echo "Running xatlas baseline smoke..."
bash scripts/baseline.sh /home/user/data/common_shapes "$SMOKE_ROOT/xatlas" "$LIMIT"
test -f "$SMOKE_ROOT/xatlas/results.json" || { echo "ERROR: xatlas smoke did not write results.json"; find "$SMOKE_ROOT" -maxdepth 3 -type f -print; exit 1; }
echo "Running PartUV method smoke..."
bash scripts/method.sh /home/user/data/common_shapes "$SMOKE_ROOT/partuv" "$LIMIT"
test -f "$SMOKE_ROOT/partuv/results.json" || { echo "ERROR: PartUV smoke did not write results.json"; find "$SMOKE_ROOT" -maxdepth 3 -type f -print; exit 1; }
echo "Comparing smoke outputs..."
bash scripts/evaluate.sh compare \
  "$SMOKE_ROOT/xatlas/results.json" \
  "$SMOKE_ROOT/partuv/results.json" \
  "$SMOKE_ROOT/scores.json"
test -f "$SMOKE_ROOT/scores.json" || { echo "ERROR: smoke comparison did not write scores.json"; exit 1; }

# Validate scores against reference
python3 validate.py --compare || true
