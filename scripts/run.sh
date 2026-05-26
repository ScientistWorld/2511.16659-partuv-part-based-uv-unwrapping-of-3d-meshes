#!/bin/bash
set -e
export TMPDIR=/dev/shm
export MPLCONFIGDIR=/dev/shm/matplotlib
cd /home/user

# Submission smoke: run one mesh through baseline, method, and evaluation.
# Full reproduction remains: PARTUV_LIMIT=0 bash scripts/reproduce.sh
LIMIT="${PARTUV_LIMIT:-1}"
export PARTUV_LIMIT

echo "=== PartUV reproduction run ==="
echo "Mesh limit: ${LIMIT:-all}"
echo "Python: $(python3 --version)"
echo "CUDA available: $(python3 -c 'import torch; print(torch.cuda.is_available())' 2>/dev/null || echo 'error')"

# Verify resources exist (these are bind-mounted from workspace at runtime)
test -f /home/user/checkpoints/partfield/model_objaverse.ckpt || { echo "ERROR: PartField checkpoint missing"; exit 1; }
test -d /home/user/data/common_shapes || { echo "ERROR: Common Shapes dataset missing"; exit 1; }

# Run end-to-end: baseline, method, and evaluation
bash scripts/reproduce.sh

# Validate scores against reference
python3 validate.py --compare || true
