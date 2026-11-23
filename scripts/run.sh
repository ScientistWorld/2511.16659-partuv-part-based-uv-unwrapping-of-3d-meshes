#!/bin/bash
# Job entry point. Reproduces the reference end to end (PartUV + xatlas through the hidden test
# and the train evaluation) and re-runs the hardening study (variants and shortcuts through the
# hidden test). See hardening/run_all.sh; scripts/reproduce.sh is the reference-only path.
set -uo pipefail
cd /home/user
bash hardening/run_all.sh
