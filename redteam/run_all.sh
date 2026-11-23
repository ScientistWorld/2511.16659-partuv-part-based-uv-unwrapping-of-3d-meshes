#!/bin/bash
# Job driver: every scenario's run.sh (method/shortcut in place, then the hidden test).
# GPU method variants run GPU_PAR at a time (default 1: jobs get one CPU); CPU shortcuts run in a second pool; the
# hidden-test step itself is serialized by a lock because all scenarios share scoring/.
# Finished scenarios (redteam/<name>/hidden_test_status.json) are skipped unless FORCE=1.
set -uo pipefail
cd /home/user
mkdir -p /home/user/checkpoints/rt/logs
echo "=== red-team job $(date -Is) ==="
echo "nproc=$(nproc)"; free -g | head -2
nvidia-smi --query-gpu=name,memory.total --format=csv 2>/dev/null || echo "no nvidia-smi"
python3 -c "import torch; print('cuda', torch.cuda.is_available(), torch.cuda.device_count())" 2>&1 | tail -1

GPU_SCEN="${GPU_SCEN:-ref_seed0 variant_lscm ref_seed1 shortcut_high_tau ref_seed2 variant_more_search variant_normals bruteforce_tau_inf variant_tau_1p5 variant_tau_1p1}"
CPU_SCEN="${CPU_SCEN:-shortcut_trivial_quad check_all_fail check_unregistered shortcut_stale_scores shortcut_keep_largest_chart shortcut_inf_uv shortcut_uv_weld shortcut_unfold shortcut_skip_hard}"

run_one() {
  local n="$1"
  if [ -f "/home/user/redteam/$n/hidden_test_status.json" ] && [ -z "${FORCE:-}" ]; then
    echo "[run_all] skip $n (done)"; return 0
  fi
  local t0=$(date +%s)
  echo "[run_all] start $n $(date -Is)"
  bash "/home/user/redteam/$n/run.sh" > "/home/user/checkpoints/rt/logs/$n.log" 2>&1
  local rc=$?
  tail -n 40 "/home/user/checkpoints/rt/logs/$n.log" > "/home/user/redteam/$n/run.log"
  echo "[run_all] done $n rc=$rc in $(( $(date +%s) - t0 ))s"
}
export -f run_one

printf '%s\n' $GPU_SCEN | xargs -P "${GPU_PAR:-1}" -I{} bash -c 'run_one {}' &
gpid=$!
printf '%s\n' $CPU_SCEN | xargs -P 1 -I{} bash -c 'run_one {}' &
cpid=$!
wait $gpid $cpid

python3 /home/user/redteam/summarize.py || echo "summarize failed"
echo "=== red-team job finished $(date -Is) ==="
