# Hardening report (iteration 11)

Gym: PartUV (part-based UV unwrapping) on Common Shapes. Every number below comes from the CPU
job `19019962-4c7`, driven by `hardening/run_all.sh`. Per-scenario details are in
`hardening/results/<scenario>.json`, and the table is in `hardening/results/summary.md`
(`python3 hardening/summarize.py` recomputes it). Every scenario was run the way the grader runs
it. Its method folder (`<dir>/unwrap.sh`) went through `scripts/evaluate_test.sh`, which takes
no arguments. Scenario roots and output files were redirected with `CHECKPOINTS_ROOT` and
`SCORES_TEST_JSON` so that the gym's own score files keep only the reference runs.

Rank proxies (the real rank normalises by the unknown spread over future attempts):
- **rel**: Σ |coef| · improvement / |reference value|.
- **spread**: Σ |coef| · improvement / std over the honest PartUV runs (reference, rerun,
  3 seeds, best-of-seeds, more search, normals, LSCM, τ = 1.1).
- **pool**: the same, divided by the std over every scenario. This is a pool dominated by failed
  attempts, and the values are shown ×10³.

"Before" numbers are from `REDTEAM.md` (old evaluator, old coefficients, spread / relative proxy).

## What changed

1. **The hidden test runs the method on meshes it has not seen.** PartUV needs no training, so
   the 12 held-out Common Shapes meshes were moved out of the workspace.
   - They now exist only in `eval/test/meshes/`: about 9 MB of xz, with sha256 checksums and
     anonymous ids. `eval/test/fetch_meshes.py` can rebuild them from the public archive.
   - `data/downloads/common_shapes/` now holds only the 12 training meshes.
   - A method is any `checkpoints/<dir>/unwrap.sh <input_dir> <output_dir>`.
     `scripts/evaluate_test.sh` (no arguments) runs **every** such folder on fresh, anonymised
     copies of the held-out meshes and scores the `uv.obj` files the method writes.
   - The evaluator code and the meshes are loaded before any method runs.
     `scores_test.json` is deleted first and written atomically at the end.
   - `scripts/evaluate_train.sh` does the same on the visible training meshes.
   - The two evaluators are self-contained copies and share no code (`eval/{train,test}/uv_eval.py`).
2. **The evaluator recomputes everything from the input mesh and the raw OBJ** (`eval/test/uv_eval.py`):
   - **Input identity.** Output vertices are matched to input vertices by position. Every output
     triangle must be an input triangle, and every non-degenerate input triangle must be present
     (quads may use either diagonal). Copies are capped at the input's own multiplicity. All 3-D
     quantities come from the input mesh.
   - **Charts.** Charts are built on input-surface edges, joined only where the output shares
     the edge's vertices (`v` or `vt` index) *and* the UVs agree. UV coincidence alone joins
     nothing.
   - **The paper's admissibility test per chart**: area distortion (Eq. 3, clipped at 10) ≤ τ = 1.25
     (+1e-3 slack), no folded interior edge, and no self-overlap. Overlap is a point-sampling
     test with a per-chart grid and a per-chart budget.
   - **The paper's angular metric**: 1 − mean |cos(tangent, bitangent)|, the official code's
     `angular_distortion_mean`. It replaces the one-corner comparison.
   - **Failure handling.** A chart that fails a constraint is scored as failed: each of its
     triangles counts as one chart, its triangles get |cos| = 1, the mesh's area distortion is
     set to 10, and the mesh is not a success. A failed mesh gets the worst value in every metric:
     charts = number of input triangles, area = 10, angular = 0. This covers no output,
     unreadable output, non-finite or |uv| > 1e9 UVs, and surface mismatch. Every value is finite.
3. **Baseline.** xatlas now unwraps a copy of each mesh scaled to a bounding-box diagonal of 100,
   and the original positions are written back. Previously xatlas returned degenerate or folded
   charts on every mesh with a diagonal under 0.5 (igea, bimba, happy, horse), because of its
   absolute tolerances.
4. **Coefficients** (`scoring/reference.json`). Only magnitudes count:

   | metric | before | after |
   |---|---|---|
   | `avg_charts` | 1.0 | 1.0 |
   | `success_rate` | 0.2 | 0.2 |
   | `median_charts` | 0.4 | 0.25 |
   | `angular_distortion` | 0.4 | 0.04 |
   | `area_distortion` | 0.35 | 0.01 |

   Why: the distortion bound and the validity checks are now hard, per-chart constraints. Below
   the bound, lower area or angular distortion comes mostly from using *more* charts: τ = 1.1 has
   the best area value (1.086), and the normals ablation is better on both. With the old weights
   the normals ablation ranked first under the spread proxy (+0.41). The paper's headline is
   chart count, with distortion "on par" with baselines. Angular keeps the larger of the two
   small weights because it is the only signal against trading conformality for fewer charts.
5. **`reference.json` baseline rows.** The paper's Table 1 numbers are unchanged. The paper's
   xatlas and Blender rows moved to `_xatlas` and `_blender`, because the paper did not hold
   baselines to τ, so they are not on the gym's scale. A metric-less `xatlas` row registers the
   gym's baseline method.
6. Documentation (`briefing/evaluation.md`, `briefing/problem.md`, `scoring/*.md`) now describes
   this interface and measurement. Dead prototypes (`method/pipeline.py`, `partuv.py`,
   `lscm_flattening.py`, `run_partuv_official.py`) and the old evaluator and registration
   manifests were removed. `scripts/run.sh` reproduces the reference end to end
   (`scripts/reproduce.sh`).

## Reference score before / after

| | success | avg charts | median | angular | area |
|---|---|---|---|---|---|
| test, before (old evaluator) | 100 | 55.42 | 22.5 | 0.9910 (old metric) | 1.3319 |
| **test, after** (`scores_test.json`, `partuv`) | 100 | **57.75** | 22.5 | 0.9854 | 1.2047 |
| train, before | 100 | 42.00 | 18.5 | 0.9889 | 1.5256 |
| **train, after** (`scores_train.json`) | 100 | **45.42** | 18.5 | 0.9800 | 1.2022 |
| paper, all 24 meshes | 100 | 48.6 | 16.5 | 0.990 | 1.283 |

The change comes from the evaluator, not the method. The PartUV code path and its outputs are
unchanged: the self-check scored the old outputs at PartUV's own chart counts. The old evaluator
merged charts that coincided in UV: on happy it counted 268 charts against PartUV's own 296, and
the merged charts inflated area distortion to 2.78. The test-split reference is valid on 12/12
meshes, with every chart ≤ τ, no folds and no overlap.

The reference ran alone, as stage 1 of the job. A second run (`ref_rerun`) reproduces it
**exactly**. PartField is forced onto the CPU and no wall-clock limit sits in the method's path.
The only limit is a 4 h hang guard, and the reference takes 894 s for all 12 meshes.

xatlas on the test split, after: success 25, avg 10148.8, median 4138, angular 0.9016, area 7.77.
Its raw chart count is about 425 per mesh. On 9/12 meshes a few of its large charts exceed τ, and
on 4 of those some charts also self-overlap; those charts are scored as failed. No xatlas chart
is folded after the scale fix.

## Does a better result now score higher?

Yes. All three proxies give the same order: best-of-seeds > more search > reference ≈ seeds >
normals ablation > τ = 1.1 > LSCM.

| run (PartUV, hidden test) | avg | median | angular | area | before (spread / rel) | after rel | after spread | after pool ×10³ |
|---|---|---|---|---|---|---|---|---|
| reference | 57.75 | 22.5 | 0.9854 | 1.2047 | 0 / 0 | 0 | 0 | 0 |
| best of 4 PartField seeds (better) | 53.67 | 17.0 | 0.9852 | 1.2021 | +0.22 / +0.17 | **+0.132** | **+0.191** | **+0.146** |
| more search: t = 20, 10 ABF iterations (better) | 54.75 | 22.0 | 0.9854 | 1.2053 | +0.09 / +0.06 | **+0.057** | **+0.089** | **+0.090** |
| normals instead of PartField (paper Tab. 4b, weaker) | 69.33 | 18.0 | 0.9877 | 1.1809 | **+0.05** / −0.10 | **−0.150** | **−0.164** | **−0.039** |
| LSCM instead of ABF++ (paper Tab. 7, weaker) | 156.58 | 71.0 | 0.9874 | 1.2138 | −3.93 / −2.67 | −2.250 | −3.374 | −3.048 |
| τ = 1.1 (stricter operating point) | 142.00 | 48.5 | 0.9886 | 1.0862 | −2.64 / −1.93 | −1.747 | −2.557 | −2.055 |
| seeds 0 / 1 / 2 | 57.8 / 58.0 / 60.4 | 23.5 / 20 / 22.5 | 0.9854 | 1.20–1.21 | | −0.013 / +0.023 / −0.046 | −0.018 / +0.033 / −0.073 | −0.009 / +0.021 / −0.083 |

Seed noise of the rank proxies (reference + 3 seeds): rel 0.025, spread 0.038, pool 0.039×10⁻³.
Seed std of avg charts is 1.11, of median 1.29.

Paired over the same 12 held-out meshes:
- **Best-of-seeds** is better on 7 meshes and worse on none. Its gain is 5 to 5.3 seed-σ (3.7σ pooled).
- **More search** is better on 6 and worse on none (2.3σ).
- **Normals** has 20% more average charts, mainly on happy (437 vs 296) and lucy (125 vs 96). It
  is better on 6 meshes and worse on 5, and better in median and distortion. It now ranks below
  the reference: 6σ (rel), 4σ (spread), about 1σ in a failure-dominated pool. Before, it tied
  or beat the reference.

## Shortcuts: fix and score before / after

All shortcuts ran through the no-argument hidden test as method folders. "After" values are
success / avg / median / angular / area, followed by the rel / spread proxy. The reference
after the fix is 100 / 57.75 / 22.5 / 0.9854 / 1.2047.

| shortcut | fix | before (spread / rel) | after | after rel / spread |
|---|---|---|---|---|
| `trivial_quad`: writes a unit square | input identity | +3.95 / +1.46 | 0 / 74303 / 83209 / 0 / 10 | −2210 / −3331 |
| `keep_largest_chart`: drops every other face | input identity (missing triangles) | +2.28 / +1.42 | 8.3 / 73804 / 83209 / 0.083 / 9.25 † | −2202 / −3314 |
| `unfold`: no cuts, isometric BFS layout that overlaps itself | per-chart overlap / fold check | +3.94 / +1.45 | 8.3 / 73804 / 83209 / 0.083 / 9.25 † | −2202 / −3314 |
| `uv_weld`: charts moved so their UV edges coincide | charts from surface edges + the output's shared vertices | +2.17 / +1.42 | identical to the reference (57.75 / 22.5) | 0.000 / +0.005 |
| `inf_uv`: extra faces with UV ≈ 1e200 | finite-UV and \|uv\| ≤ 1e9 check; extra faces are off-surface | +0.12 / +0.09 | 0 / 74303 / 83209 / 0 / 10 | −2210 / −3331 |
| `skip_hard`: no output for meshes with > 200 charts | failed mesh gets the worst value in every metric | +0.70 / +0.39 | 91.7 / 8249.8 / 22.5 / 0.904 / 1.934 | −142 / −227 |
| `tau_1p5` (operating point; τ = 2.0 behaved the same before) | τ = 1.25 enforced per chart, violating charts scored as failed | +0.29 / +0.32 (τ = 2.0: +0.36 / +0.40) | 16.7 / 18316.5 / 12991 / 0.720 / 8.52 | −461 / −708 |
| `tau_inf` (brute force: fewest charts the overlap check allows) | same | −1.56 / −0.27 | 16.7 / 45437 / 27435 / 0.425 / 8.52 | −1091 / −1678 |
| `stale_scores`: hand-written `scores_test.json` + ghost method that crashes the test | file deleted at start, written atomically; no registration step | +2.88 / +1.37 | normal run: fabricated file replaced by the real scores; early failure (rc = 1): no file left (`shortcut_stale_scores.json`) | n/a |
| `constant_uv_nan`: NaN poison | \|uv\| ≤ 1e9, all aggregates finite | +2.21 / +1.45 | 0 / 74303 / 83209 / 0 / 10 | −2210 / −3331 |
| `constant_uv`: every UV = (0.5, 0.5) | zero-area UV triangles count 10 and are folds | −86.2 / +1.27 | 0 / 74303 / 83209 / 0 / 10 | −2210 / −3331 |
| `copy_input`, `all_fail` | worst finite values instead of `Infinity` | inf values | 0 / 74303 / 83209 / 0 / 10 | −2210 / −3331 |
| `unregistered`: method folder added after the last train eval | every folder with `unwrap.sh` is run | absent from scores | both methods scored (`check_unregistered.json`) | n/a |
| new `fold_one`: one vertex pushed outside its 1-ring | fold check | n/a | 0 / 9820 / 8347 / 0.747 / 10 | −262 / −404 |
| new `shatter`: one chart per triangle (worst valid output) | n/a (sanity) | n/a | 100 / 74303 / 83209 / 1.0 / 1.0 | −2210 / −3294 |

† The one success is mesh_01 (the flat alligator), which a single chart already solves.

No hand-written rule or closed form comes near the reference. Brute force (τ → ∞, no cuts,
one chart per triangle) ranks thousands of proxy units below it.

## Headroom check

- **At the bound:** `success_rate` = 100 for the reference.
- **Room left:**
  - avg charts 57.75 and median 22.5, against a lower bound of about one chart per connected component;
  - angular 0.9854 (bound 1);
  - area 1.2047 (bound 1.0).
- **Better than the reference:** two honest variants of the paper's own search, best-of-seeds and
  more search, beat it beyond seed noise and paired per mesh.
- **No variant reaches a bound.** The best one still has 53.7 average charts.
- **Brute force fails:** the brute force the paper avoids (no cuts, or τ → ∞) collapses under the
  constraints.

No extra experiment was needed.

## Shortcuts and weaknesses left (and why)

1. **More compute per mesh pays** (best-of-N restarts, deeper search). Here it is honest
   improvement: the method really runs on unseen meshes inside the hidden test. Runtime is not
   scored because it is hardware dependent, and a time limit would make the stored reference
   depend on machine load. The only limit is the 4 h hang guard.
2. **Conformality is guarded only by a coefficient.**
   - The paper's angular metric measures orthogonality only. It is blind to an axis-aligned
     anisotropic stretch (self-check `stretch_u`).
   - A method that trades conformality for charts (e.g. an area-preserving flattener) pays only
     through `angular_distortion` (0.04). Under the honest-spread proxy, a drop of 0.035 in
     angular costs about as much as 40 fewer average charts gain.
   - No hard angular bound was added: the paper defines none, and honest per-chart values (up to
     0.235 mean |cos| on a normals chart) overlap shortcut values (0.228 at τ = 1.5).
3. **Rank normalisation.** In a pool dominated by failed attempts (worst chart count is about
   74k), honest differences shrink to about 10⁻⁴. The chosen coefficients keep the right order
   there too, but normals vs the reference is only about 1σ apart in that regime.
4. **The held-out meshes are public Common Shapes models.** Inputs are anonymised but not
   perturbed, so a method could fingerprint them (e.g. by face count) and apply per-mesh
   settings. During the hidden test a method can also read the workspace and copy the inputs.
   There are no answers to read. Both are forbidden in `CONSTRAINTS.md` and left to the grader.
5. **τ slack of 1e-3.** A method could run at τ = 1.251 internally. The gain is negligible.
6. **Overlap sampling.** The overlap test samples about 6 points per triangle per chart. A
   self-overlap smaller than a sample cell can be missed. Folds are checked exactly on every
   interior edge.
7. **`area_distortion` is largely redundant** with the per-chart τ bound and carries little weight.

## Could not fix / limitations, stated plainly

- Seam length and overall atlas distortion are not scored: there is no UVPackMaster packing
  (proprietary), and outputs are un-packed.
- The test is 12 Common Shapes meshes, a split of the paper's 24-mesh set. The paper's other
  three datasets are not included. Blender, Open3D, Nuvo and OptCuts are not reproduced, and the
  PaMO distortion surrogate is off. These are the same limitations as before.
- The gym's xatlas is not the paper's xatlas: the paper does not hold baselines to τ, and the
  run settings differ. Its numbers are not comparable with Table 1.
- **Job infrastructure.** The job ran on preemptible 1-hour nodes and was resumed per scenario.
  The reference's stage-1 hidden test ran alone and uninterrupted. Before handing over, the
  hardening cache (which held copies of the held-out meshes) and the legacy outputs
  (`checkpoints/_legacy`) were deleted, so no held-out geometry remains outside `eval/test/`.
