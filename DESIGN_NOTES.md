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

## Runtime Concerns For Next Iteration

- The new percentile metrics are implemented but not numerically exercised in this design-only pass. The runner should verify that `scores_train.json` and `scores_test.json` include `p05_angular_distortion` and `p95_area_distortion` for every scored method.
- The evaluators intentionally rescore existing UV OBJ artifacts instead of rerunning methods. A future method that only writes visible-train mesh outputs should receive failures on held-out meshes, which is the desired anti-shortcut behavior.
- The split is 12 visible / 12 held-out Common Shapes meshes. This is useful for method-overfit detection, but still small; percentile metrics may be somewhat coarse with 12 meshes.
