#!/bin/bash
# Job entry point: reproduce the reference end to end -- register PartUV and xatlas as methods,
# run the hidden test (held-out meshes) and the train evaluation. The hardening study that
# re-ran variants and shortcuts through the hidden test is hardening/run_all.sh.
set -uo pipefail
cd /home/user
bash scripts/reproduce.sh
