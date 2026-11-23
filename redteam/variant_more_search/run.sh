#!/bin/bash
# Stronger-search variant: Heuristic-1 chart limit t=20 (paper t=10) and 10 ABF iterations (C++ default; gym config uses 5).
bash /home/user/redteam/lib/run_variant.sh variant_more_search --set unwrap.agg_parts=20 --set unwrap.abf_iters=10
