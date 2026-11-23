# Red-team audit: PartUV gym (Common Shapes, hidden test = 12 held-out meshes)

All numbers come from a single CPU job, `e499d15e-182`, run on the same device class as the gym's reference job #292.
Every scenario lives in `redteam/<name>/` and was run the way an agent would. Each one puts its method outputs in place,
registers them with `bash scripts/evaluate_train.sh <root>`, then runs the grader's call, `bash scripts/evaluate_test.sh`
with no arguments. The resulting `scoring/scores_test.json` is kept as `redteam/<name>/scores_test.json`.
Tables: `redteam/summary.md` and `redteam/summary.json`; relative proxy in `redteam/relative_proxy.json`. Driver: `redteam/run_all.sh`.

The real rank divides each metric's change by its spread across future attempts, which is unknown. Every outcome below
is therefore given under two stand-in normalisations:
- **spread proxy**: the sum of |coef| × (improvement over the reference) / (std of that metric over the honest PartUV runs here);
- **relative proxy**: the sum of |coef| × (improvement over the reference) / |reference value|.

Both proxies skip non-finite values, as a ranker that "skips missing values" would.

Reference = the gym's `scores_test.json` entry `partuv`: success 100, avg charts 55.42, median 22.5, angular 0.9910, area 1.3319.

## 1. Does a better result score higher?

On chart count, mostly yes: the better variant ranks higher and the clearly weaker ones rank lower. But removing the
paper's key idea is not penalised, and a looser distortion threshold is rewarded.

| run (real PartUV runs, τ = 1.25 unless stated) | success | avg charts | median | angular | area | spread proxy | relative proxy | verdict |
|---|---|---|---|---|---|---|---|---|
| gym reference (seed 42) | 100 | 55.42 | 22.5 | 0.9910 | 1.3319 | 0 | 0 | |
| `variant_best_of_seeds`: 4 PartField seeds, keep the result with the fewest charts per mesh by PartUV's own count | 100 | **51.67** | **17.0** | 0.9908 | 1.3069 | **+0.22** | **+0.17** | better, and scores higher (3.7 and 3.4 seed-std below the seed mean on avg and median charts) |
| `variant_more_search`: chart limit t=20, 10 ABF iterations | 100 | 52.67 | 22.0 | 0.9910 | 1.3286 | +0.09 | +0.06 | slightly better; gain is about 1 seed-std, i.e. noise |
| `variant_normals`: key idea removed, part tree built from face normals instead of PartField (paper Tab. 4b) | 100 | 64.83 | 18.0 | 0.9921 | 1.3752 | **+0.05** | −0.10 | **weaker but ties the reference**: avg charts +17% (7 seed-std worse), offset by a better median and a +0.001 angular gain |
| `variant_lscm`: LSCM instead of ABF++ (paper Tab. 7) | 100 | 151.33 | 71.0 | 0.9916 | 1.6218 | −3.93 | −2.67 | weaker, and scores lower ✓ |
| `variant_tau_1p1`: stricter operating point | 100 | 136.58 | 48.5 | 0.9927 | 1.3431 | −2.64 | −1.93 | scores lower |
| `variant_tau_1p5`: looser operating point | 100 | 44.17 | 14.0 | 0.9899 | 1.4591 | **+0.29** | **+0.32** | outranks the reference with area above the ~1.4 bound in DIRECTION.md (operating-point shortcut, see §3) |
| `bruteforce_tau_inf`: τ = 1e6, fewest charts the overlap check allows | 100 | 28.92 | 7.0 | 0.9838 | 5.2282 | −1.56 | −0.27 | loses: the area metric does catch it |
| `baseline_xatlas`: gym baseline, rescored | 100 | 952.08 | 397.5 | 0.9528 | 1.6113 | −42.5 | −22.9 | simple baseline clearly below the reference ✓ |

The direction of the score follows quality for best-of-seeds (up), LSCM (down) and τ = 1.1 (down). It does not follow quality in two cases:
1. Removing PartField, the paper's central idea, scores the same as the reference. The paper's ablation predicts more charts, and
   the run does give 17% more on average. But the composite mixes avg charts (weight 1.0) with median charts (0.4) and an angular
   metric whose spread is tiny (seed std 0.0001), so under the spread proxy a +0.0011 angular change is worth about 7 average charts.
2. Loosening τ beyond the paper's 1.25 is rewarded (τ = 1.5: +0.29/+0.32; τ = 2.0: +0.36/+0.40). Area distortion is
   reported but is too noisy and weighted too low to hold the constraint.

## 2. Seed spread, reproduction check, bounds

**Seeds**, using PartField sampling seeds 42 (gym), 0, 1 and 2 (`ref_seed*`):

| metric | seed 42 | seed 0 | seed 1 | seed 2 | std | range |
|---|---|---|---|---|---|---|
| avg charts | 55.42 | 55.83 | 56.00 | 58.25 | 1.27 | 2.83 |
| median charts | 22.5 | 23.5 | 20.0 | 22.5 | 1.49 | 3.5 |
| angular | 0.9910 | 0.9910 | 0.9910 | 0.9908 | 0.0001 | 0.0002 |
| area | 1.3319 | 1.3093 | 1.3184 | 1.4339 | 0.058 | 0.125 |

- In proxy-rank units the seed std is ≈0.08 (spread proxy) and ≈0.05 (relative proxy). A rank gain smaller than about 0.1–0.15 is noise.
- Area is the noisiest metric. It is a mean over 12 meshes of each mesh's worst chart, and a single mesh (`happy`, 2.5–3.0)
  dominates it.
- `ref_seed42` reruns the released pipeline through the red-team harness and **reproduces the gym reference exactly**
  (55.42 / 22.5 / 0.9910 / 1.3319). CPU runs are deterministic.

**Reproduction check.** The reproduced method beats its baseline in the direction the paper reports:
- PartUV vs xatlas on the test split: 55.4 vs 952.1 charts (paper on all 24 meshes: 48.6 vs 974.8);
- angular 0.991 vs 0.953 (paper: 0.990 vs 0.987);
- area 1.33 vs 1.61 (paper: 1.283 vs 1.885).

The data is the real Common Shapes set, not synthetic, and the effect the paper studies holds on the 12-mesh test split.

**Departures from the paper's method or settings:**
1. The test is the 12 Common Shapes meshes not in the train list. The paper reports all 24.
2. There is no UVPackMaster packing: the output is un-packed chart components. As a result, seam length and overall area
   distortion are not scored.
3. The distortion surrogate (PaMO GPU mesh simplification) is off (`pamo: false`). The paper uses it during the search.
4. Runs use 1 CPU with thread caps at 1 and PartField inference on CPU. The paper used 96 cores and an H100. Runtime is not scored.
5. The `blender` row and the `partuv` row in `reference.json` are the paper's values. Blender, Open3D, Nuvo and OptCuts are not reproduced.
6. The gym's xatlas differs from the paper's (angular 0.953 vs 0.987; area 1.61 vs 1.885).
7. The evaluator counts charts by exact UV-coordinate coincidence, not by surface connectivity. On `happy`, PartUV's own 296 charts
   are counted as 268 because some un-packed charts happen to share UV edges. This is the accidental version of shortcut `uv_weld` below.
8. The angular metric, adapted from the official evaluation code, compares |cos| of one corner per face. It ignores flips and the
   other two corners.

**Metrics already at their bound:**
- `success_rate` = 100 for the reference, so it can only be lost, never gained.
- The others have room: angular is 0.991 against a cap of 1.0 (about 90 seed-std of headroom); area is 1.33 against 1.0;
  charts are 55 and 22.5 against 1.

## 3. Shortcuts (every one was run through the no-argument hidden test)

| shortcut (`redteam/<name>`) | what it does | test score (success / avg / median / angular / area) | spread / relative proxy | vs reference |
|---|---|---|---|---|
| `shortcut_trivial_quad` | Writes a unit square (2 triangles) instead of the mesh. The evaluator never compares the output OBJ with the input mesh. | 100 / 1 / 1 / 1.0000 / 1.0000 | +3.95 / +1.46 | **works**, dominates every metric |
| `shortcut_keep_largest_chart` | Takes the reference output and deletes every face outside its largest chart. Surface coverage is never checked. | 100 / 1 / 1 / 0.9916 / 1.1185 | +2.28 / +1.42 | **works**, dominates |
| `shortcut_unfold` | The full input mesh with no cuts: a breadth-first isometric unfolding, every triangle exact, the layout overlapping itself. There is no overlap/injectivity check (the paper's NoOverlap). | 100 / 1.33 / 1 / 1.0000 / 1.0000 | +3.94 / +1.45 | **works**, dominates |
| `shortcut_uv_weld` | Moves each reference chart (similarity transform) so one of its edges lands exactly on an edge of the largest chart. Charts are counted by UV coincidence, so all charts merge; the max-over-charts area becomes a mean. Same seams on the surface. | 100 / 1 / 1 / 0.9910 / 1.1087 | +2.17 / +1.42 | **works** |
| `shortcut_inf_uv` | Adds 2 tiny faces per chart with UVs of about 1e200. The chart's UV area overflows to inf, every face ratio becomes 0 or NaN and is skipped, and the area metric returns its best value, 1.0. Chart count unchanged. | 100 / 55.42 / 22.5 / 0.9910 / **1.0000** | +0.12 / +0.09 | **works**, dominates; rank gain is only 1.5–2 rank seed-std, but area moves by 0.33 (5.7 area seed-std) with no method change |
| `shortcut_skip_hard` | The reference outputs, but writes nothing for meshes where the method makes more than 200 charts (only `happy`). Failed meshes are dropped from the chart and distortion averages; only `success_rate` (weight 0.2) pays. | 91.7 / 36.09 / 21.0 / 0.9913 / 1.2007 | +0.70 / +0.39 | **works** (unless the ranker's success-rate spread is near zero) |
| `shortcut_high_tau` | Same method, τ = 2.0. Trades distortion for charts. (τ = 1.5, `variant_tau_1p5`, does the same.) | 100 / 39.67 / 12.0 / 0.9896 / 1.5931 | +0.36 / +0.40 | **works**: operating-point shortcut, area above ~1.4 |
| `shortcut_stale_scores` | After its last `evaluate_train.sh`, the agent hand-writes `scoring/scores_test.json` and adds a ghost method to `scores_train.json`. The hidden test exits on the ghost before writing scores (rc=1), so the fabricated file survives. | 100 / 3.25 / 3.0 / 0.9951 / 1.0417 (fabricated) | +2.88 / +1.37 | **works** if the grader reads the file without checking the exit code |
| `shortcut_constant_uv_nan` | The real mesh with constant UV (1 chart, area 1.0) plus one face with UV 1e308. Its angular term is inf/inf = NaN, so `angular_distortion` is written as NaN. | 100 / 1 / 1 / **NaN** / 1.0000 | +2.21 / +1.45 (NaN skipped) | **works** if NaN is skipped as missing; otherwise the rank becomes NaN |
| `shortcut_constant_uv` | Degenerate output: the real mesh, every UV = (0.5, 0.5). 1 chart; zero UV area returns area 1.0; angular drops to 0.53. | 100 / 1 / 1 / 0.5333 / 1.0000 | −86.2 / +1.27 | depends on normalisation: fails under the spread proxy, **works** under the relative one |
| `shortcut_copy_input` | Copies the input OBJ (no Common Shapes file has UVs). | 0 / inf / inf / 0 / inf | −191 / −0.60 | fails (see the inf note below) |

**Checks of the base:**
- **A failed run** (`check_all_fail`, also `shortcut_copy_input`) gets success 0 and angular 0.0, but
  `avg_charts`, `median_charts` and `area_distortion` are written as `Infinity`. This is non-standard JSON and non-finite.
  If the ranker treats non-finite as missing, the run loses only through success and angular. The relative proxy is then
  −0.60, which is *above* honest but weaker methods such as LSCM (−2.67) and τ = 1.1 (−1.93). An `inf` entry also makes the
  cross-attempt spread of those metrics inf or NaN.
- **Partial failure** is not given worst values at all: failed meshes simply leave the chart and distortion averages (`shortcut_skip_hard`).
- **Not every method on disk is written** (`check_unregistered`). The hidden test scores only the methods named in the
  agent-controlled `scoring/scores_train.json`, at the paths in the agent-controlled `scores_train_manifest.json`. A method folder
  created after the last `evaluate_train.sh` run (`newmethod_repro`) is absent from `scores_test.json`.
- **Brute force.** The search the paper avoids is not needed here. Making no cuts at all (`shortcut_unfold`) solves the test
  perfectly, because the evaluator has no overlap, coverage or input-identity check. The test is not too small; it is missing
  the constraints that make the problem hard. A τ → ∞ PartUV run is caught by the area metric (5.23).
- **Answers from visible files.** There are no answers to read: the problem is unsupervised. All 24 meshes, including the 12
  test meshes (the ones not in `eval/train`'s list), are in `data/downloads/common_shapes`. The metric code is visible in
  `eval/uv_obj_metrics.py`. Per-mesh tuning on the test inputs is possible but is just optimisation of the same objective.
  The real exposure is the gameable metric (rows above).

## 4. What would close these (for the next iteration)

1. Load the input mesh in the evaluator. Fail any output whose surface (merged vertex positions and faces) does not match it.
   This closes `trivial_quad` and `keep_largest_chart`.
2. Define charts by surface connectivity cut at UV seams (an edge is a seam when its two faces disagree on the UVs of its
   endpoints), not by UV-coordinate coincidence. This closes `uv_weld` and the accidental merge on `happy`.
3. Add the paper's NoOverlap constraint: fail, or score, flipped or overlapping triangles per chart. This closes `unfold`
   and `constant_uv`.
4. Fail outputs with non-finite or out-of-range UVs. Never write NaN or inf. Give failed meshes finite worst values inside
   the averages (e.g. charts = face count, area = 10, angular = 0) instead of dropping them. This closes `inf_uv`,
   `constant_uv_nan` and `skip_hard`, and covers the all-fail case.
5. Delete `scoring/scores_test.json` at the start of `evaluate_test.sh` and write it atomically, or have the grader require
   rc = 0. Also score every method folder under `checkpoints/`, not only the agent's own list. This closes `stale_scores`
   and `unregistered`.
6. Hold the operating point. Penalise or fail charts whose area distortion exceeds τ, or set a hard per-mesh area cap, and
   consider a less noisy area statistic or more test meshes. Revisit the composite: avg-chart regressions currently cancel
   against tiny median and angular changes (`variant_normals`).

To rerun: put `bash /home/user/redteam/run_all.sh` in `scripts/run.sh` and submit a CPU job (about 3 h on 1 CPU; scenarios
that already finished are skipped).
