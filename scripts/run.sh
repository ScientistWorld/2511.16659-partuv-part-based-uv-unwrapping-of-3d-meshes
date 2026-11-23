#!/bin/bash
# Red-team audit job (temporary; restored with git when the audit is done).
set -uo pipefail
cd /home/user
bash /home/user/redteam/run_all.sh
