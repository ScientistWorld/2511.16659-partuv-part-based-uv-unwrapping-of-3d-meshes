#!/bin/bash
# Development scoring on the visible split: same as scripts/evaluate_train.sh.
set -euo pipefail
exec bash /home/user/scripts/evaluate_train.sh "$@"
