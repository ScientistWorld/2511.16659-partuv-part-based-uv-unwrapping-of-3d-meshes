#!/bin/bash
set -euo pipefail
export TMPDIR=/dev/shm
export MPLCONFIGDIR=/dev/shm/matplotlib
export PYTHONFAULTHANDLER=1
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export OPENBLAS_CORETYPE="${OPENBLAS_CORETYPE:-GENERIC}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"
export NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}"
cd /home/user

# Submission smoke: run one mesh through baseline, method, and evaluation.
# Full reproduction remains: PARTUV_LIMIT=0 bash scripts/reproduce.sh
LIMIT="${PARTUV_LIMIT:-1}"
SMOKE_ROOT="${PARTUV_SMOKE_ROOT:-/home/user/checkpoints/smoke}"

echo "=== PartUV reproduction run ==="
echo "Mesh limit: ${LIMIT:-all}"
echo "Python: $(python3 --version)"
echo "Thread caps: OMP=$OMP_NUM_THREADS OPENBLAS=$OPENBLAS_NUM_THREADS OPENBLAS_CORETYPE=$OPENBLAS_CORETYPE MKL=$MKL_NUM_THREADS NUMEXPR=$NUMEXPR_NUM_THREADS"

probe_import() {
  local module="$1"
  echo "Import probe: $module"
  python3 -m pip show "$module" 2>/dev/null | sed -n '1,6p' || true
  set +e
  python3 -X faulthandler -c "import importlib; m = importlib.import_module('$module'); print('Import OK: $module ' + str(getattr(m, '__version__', 'unknown')), flush=True)"
  local status=$?
  set -e
  if [ "$status" -ne 0 ]; then
    echo "ERROR: import probe failed for $module with exit status $status"
    exit "$status"
  fi
}

probe_import numpy
probe_import xatlas
probe_import trimesh

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
