#!/bin/bash
# Reproduce the gym reference end to end: register PartUV and xatlas as methods, score them on
# the visible training meshes and on the hidden held-out meshes.
set -euo pipefail
cd /home/user
export TMPDIR=/dev/shm
bash scripts/install_methods.sh
bash scripts/evaluate_test.sh
bash scripts/evaluate_train.sh
cp scoring/scores_test.json scoring/scores.json
python3 -m json.tool scoring/scores_train.json > /dev/null
python3 -m json.tool scoring/scores_test.json > /dev/null
