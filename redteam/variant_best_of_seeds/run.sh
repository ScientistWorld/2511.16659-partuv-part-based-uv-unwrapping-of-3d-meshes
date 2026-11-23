#!/bin/bash
# Better variant (more search, same method): run PartUV with 4 PartField sampling seeds (42 = gym reference
# outputs, 0, 1, 2 = ref_seed* runs) and keep, per mesh, the result with the fewest charts according to
# PartUV's own run_summary.json (every candidate already satisfies the tau=1.25 distortion bound).
# Needs ref_seed0..2 to have run first (run_all.sh orders it after them).
bash /home/user/redteam/lib/run_shortcut.sh variant_best_of_seeds
