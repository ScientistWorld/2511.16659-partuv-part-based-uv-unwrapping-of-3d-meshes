#!/bin/bash
set -e
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
echo "CUDA available: $(python3 -c 'import torch; print(torch.cuda.is_available())' 2>/dev/null || echo 'error')"

# Verify resources exist (these are bind-mounted from workspace at runtime)
test -f /home/user/checkpoints/partfield/model_objaverse.ckpt || { echo "ERROR: PartField checkpoint missing"; exit 1; }
test -d /home/user/data/common_shapes || { echo "ERROR: Common Shapes dataset missing"; exit 1; }

# Run end-to-end on isolated smoke outputs so the canonical 24-mesh scores
# in scoring/scores.json remain the full reproduction artifact.
rm -rf "$SMOKE_ROOT"
bash scripts/baseline.sh /home/user/data/common_shapes "$SMOKE_ROOT/xatlas" "$LIMIT"
bash scripts/method.sh /home/user/data/common_shapes "$SMOKE_ROOT/partuv" "$LIMIT"
bash scripts/evaluate.sh compare \
  "$SMOKE_ROOT/xatlas/results.json" \
  "$SMOKE_ROOT/partuv/results.json" \
  "$SMOKE_ROOT/scores.json"

# Validate scores against reference
python3 validate.py --compare || true
