#!/bin/bash
set -e
export TMPDIR=/dev/shm
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libstdc++.so.6
cd /home/user

PARTUV_LIMIT="${PARTUV_LIMIT:-6}"
export PARTUV_LIMIT

echo "=== PartUV official reproduction smoke run ==="
echo "Mesh limit: ${PARTUV_LIMIT}"
echo "Python: $(python3 --version)"

bash scripts/reproduce.sh

python3 validate.py --compare
