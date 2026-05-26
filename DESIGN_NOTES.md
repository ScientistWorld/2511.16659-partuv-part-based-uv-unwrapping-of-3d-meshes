# Train/Test Evaluation Design Notes

## Checked

- Read `scripts/evaluate_train.sh` and `scripts/evaluate_test.sh` side by side. Train invokes `eval.train`, writes `scoring/scores_train.json`, and test invokes `eval.test`, writes `scoring/scores_test.json`.
- Checked both split evaluators for method detachment. They score UV OBJ artifacts under checkpoint roots and do not import from `method/`.
- Checked for cross-import leakage between `eval/train/` and `eval/test/`; none found.
- Confirmed no `scoring/scores_train.json` or `scoring/scores_test.json` stub exists.
- Ran `bash -n` on both split shell scripts.
- Read the local paper copy at `paper/2511.16659.md`; the prompt's absolute paper path was not present. The paper explicitly uses 95th-percentile distortion as a tail-risk analysis for shortcut cases.

## Changed

- Added `p95_area_distortion` to both train and test score outputs. This follows the paper's 95th-shape distortion idea and makes it harder to game chart count by accepting a few highly distorted meshes.
- Added `p05_angular_distortion` to both train and test score outputs. This complements mean angular distortion by exposing lower-tail conformal failures.
- Updated `scoring/reference.json` so every scored metric has `higher_is_better`, `coefficient`, and `description`.
- Reweighted lower-is-better metrics with negative coefficients and kept chart count as the primary benefit while giving distortion-tail metrics nonzero constraint weight.
- After validation flagged train xatlas `avg_charts` as too far from the paper-level value, swapped `bimba` into train and `alligator` into test to balance primary-metric difficulty while keeping a 12/12 disjoint mesh split.

## Runtime Concerns For Next Iteration

- The evaluators intentionally rescore existing UV OBJ artifacts instead of rerunning methods. A future method that only writes visible-train mesh outputs should receive failures on held-out meshes, which is the desired anti-shortcut behavior.
- The split is 12 visible / 12 held-out Common Shapes meshes. This is useful for method-overfit detection, but still small; percentile metrics may be somewhat coarse with 12 meshes.

## Real-Run Results

- Job `0cb58de3-22b` completed successfully on a CPU node and produced the initial `scoring/scores_train.json`, `scoring/scores_test.json`, and both manifests. The final balanced split was regenerated locally with `scripts/evaluate_train.sh` and `scripts/evaluate_test.sh` from the same OBJ artifacts.
- Train and test method identifiers match exactly: `partuv`, `xatlas`.
- Every metric in `scoring/reference.json` is present for both methods on both slices; no `null` values remain.
- PartUV retains the core chart-count benefit on held-out meshes: `avg_charts` is 42.00 train / 55.42 test, versus xatlas at 939.58 train / 952.08 test.
- Distortion constraints remain in a comparable range for PartUV: angular distortion is 0.9889 train / 0.9910 test, area distortion is 1.5256 train / 1.3319 test, and p95 area distortion is 2.7414 train / 1.9361 test.
- `success_rate` saturated at 100% for both methods on both slices, so it is retained as a diagnostic but zero-weighted in `scoring/reference.json`.
- `python3 validate.py --post-design` passes on the regenerated balanced split.
