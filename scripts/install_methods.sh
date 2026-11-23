#!/bin/bash
# Register the reference method and the baseline as "methods on disk": a method is any folder
# checkpoints/<dir>/ holding unwrap.sh (called as: bash unwrap.sh <input_dir> <output_dir>).
set -euo pipefail
cd /home/user
mkdir -p checkpoints/partuv_repro checkpoints/xatlas_repro
cat > checkpoints/partuv_repro/unwrap.sh <<'SH'
#!/bin/bash
# Reference: PartUV, released pipeline, tau = 1.25 (method/unwrap.sh)
exec bash /home/user/method/unwrap.sh "$1" "$2"
SH
cat > checkpoints/xatlas_repro/unwrap.sh <<'SH'
#!/bin/bash
# Baseline: xatlas (baseline/unwrap.sh)
exec bash /home/user/baseline/unwrap.sh "$1" "$2"
SH
echo "install_methods.sh: registered checkpoints/partuv_repro and checkpoints/xatlas_repro"
