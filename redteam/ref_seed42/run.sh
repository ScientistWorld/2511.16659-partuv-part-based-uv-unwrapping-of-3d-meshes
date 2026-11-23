#!/bin/bash
# Harness check: reference PartUV (released pipeline, tau=1.25) with the released default PartField seed 42,
# i.e. the same settings as the gym's checkpoints/partuv_repro. Should reproduce the gym reference test score.
bash /home/user/redteam/lib/run_variant.sh ref_seed42 --seed 42
