# Experiment Overview

This file describes what each experiment in `scores_train.json` / `scores_test.json` establishes.
Each experiment corresponds to a key in the `experiments` object of those files.

## common_shapes_comparison

**What it tests:** whether a UV unwrapping method cuts meshes into fewer charts than a standard
baseline while every chart stays valid: continuous, injective (no folds, no self-overlap) and
within the fixed area-distortion bound of 1.25, with low angular distortion.

**Scientific purpose:** chart count and distortion trade off against each other. The bound
fixes the operating point, so a lower chart count is only a gain when it comes with valid
charts; a chart that breaks the bound or overlaps itself is scored as if every one of its
triangles were a separate chart, with worst distortion values.

**Primary metric:** `avg_charts` (lower is better). Also scored: `median_charts` (lower),
`angular_distortion` (higher), `area_distortion` (lower) and `success_rate` (higher).

**How it is run:** the hidden test (`scripts/evaluate_test.sh`, no arguments) runs every method
folder `checkpoints/<name>/unwrap.sh` on 12 held-out Common Shapes meshes that only `eval/test/`
holds, and scores the UV OBJs written; `scripts/evaluate_train.sh` does the same on the 12
visible training meshes. Charts are found from the input mesh's edges and the output's UVs; all
3-D quantities come from the input mesh; failed meshes get the worst value of every metric.
Seam length, overall atlas distortion and runtime are not scored (packing and hardware
dependent).
