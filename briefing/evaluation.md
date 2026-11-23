# Evaluation

## Task interface

A method is a folder `checkpoints/<name>/` containing an entry script `unwrap.sh`:

```
bash checkpoints/<name>/unwrap.sh <input_dir> <output_dir>
```

`<input_dir>` holds triangle meshes as `<id>.obj` (no UVs). For each one the method must write
`<output_dir>/<id>/uv.obj`: an OBJ with `v`, `vt` and `f v/vt ...` records that keeps the input
surface (same vertex positions and the same triangles; vertices may be duplicated along seams and
quads may be split along either diagonal), gives every face corner a UV coordinate, and shares
vertex (or `vt`) indices between the triangles of a chart. Charts are
not packed: each chart may sit anywhere in UV space, at any scale.

- `scripts/evaluate_train.sh` (no arguments) runs every method folder on the 12 visible
  training meshes (`data/downloads/common_shapes/`), keeps the outputs in
  `checkpoints/<name>/train_outputs/` and writes `scoring/scores_train.json`.
  `UV_TRAIN_REUSE=1` rescores existing outputs without rerunning the method.
- `scripts/evaluate_test.sh` (no arguments) is the hidden test. It runs every method folder on
  12 held-out meshes that are not in the workspace, scores the UV OBJs written, and writes
  `scoring/scores_test.json`. The method sees only the input meshes (anonymous file names). No
  time limit is scored; a hang guard of several hours stops a method that never returns.

The method name in the score files is the folder name without a trailing `_repro`
(the reference is `checkpoints/partuv_repro`, the baseline `checkpoints/xatlas_repro`).

## What is measured (per mesh)

1. **Surface integrity.** Output vertices are matched to the input by position (tolerance 1e-5 of
   the bounding-box diagonal); every output triangle must be an input triangle, every
   non-degenerate input triangle must appear exactly once, and every UV must be finite
   (|u|, |v| <= 1e9). All 3-D quantities are computed on the input mesh. An output that fails
   this is a **failed mesh**.
2. **Charts.** Two triangles that share an edge of the input mesh belong to the same chart when
   the output joins them along that edge -- both endpoints are the same output vertex (same `v`
   index) or carry the same `vt` index in the two triangles -- and the UVs agree. Charts are the
   connected components of this relation. Separate vertex copies that merely happen to have the
   same UV do not join triangles, and triangles that touch in UV space without being neighbours
   on the surface are never joined. (Any standard OBJ export shares vertices inside a chart.)
3. **Chart constraints.** A chart is valid when
   - its area distortion is at most 1.25 (fixed by the evaluator; 1e-3 numerical slack), where
     area distortion = mean over the chart's triangles of max(s, 1/s),
     s = (UV area / 3-D area) / (chart UV area / chart 3-D area), each triangle's value clipped
     at 10, a zero-area UV triangle counting 10;
   - no interior edge is folded: the two triangles of every continuous edge lie on opposite
     sides of it in UV;
   - it does not overlap itself in UV (point-sampling test on a per-chart grid).
4. **Scores of a mesh.**
   - `charts`: number of valid charts + number of triangles in invalid charts (an invalid chart
     is counted as if each of its triangles were its own chart).
   - `area distortion`: the largest area distortion over the mesh's charts; 10 if any chart is
     invalid.
   - `angular score`: 1 - mean over triangles of |cos| of the angle between the tangent and
     bitangent vectors (the 3-D images of the UV axes); 1.0 = conformal. Triangles of invalid
     charts count |cos| = 1.
   - A mesh is a **success** when the output passes integrity and every chart is valid.
   - A failed mesh (no output, unreadable, non-finite UVs, surface mismatch) gets the worst
     value of every metric: charts = number of input triangles, area distortion = 10,
     angular score = 0.

## Scored metrics (`common_shapes_comparison`)

| metric | direction | aggregation over the 12 meshes |
|---|---|---|
| `success_rate` | higher | % of meshes that are a success |
| `avg_charts` | lower | mean of per-mesh `charts` |
| `median_charts` | lower | median of per-mesh `charts` |
| `angular_distortion` | higher | mean of per-mesh angular score |
| `area_distortion` | lower | mean of per-mesh area distortion |

All values are finite. Coefficients are in `scoring/reference.json`: chart count dominates
(`avg_charts` 1.0, `median_charts` 0.25, `success_rate` 0.2); area (0.01) and angular (0.04)
distortion carry small weights because the distortion bound and the validity checks are
enforced per chart, and below the bound lower distortion mostly comes from using more charts.

Not scored: seam length and overall (atlas) area distortion, which depend on a packing stage the
gym does not standardise, and runtime, which depends on hardware.

## Baselines and targets

- **xatlas** (`checkpoints/xatlas_repro`, run on a copy of each mesh scaled to a bounding-box
  diagonal of 100): greedy chart growing + LSCM. It does not bound per-chart area distortion, so
  on 9 of the 12 held-out meshes some of its charts fail the 1.25 bound.
- Published reference levels on all 24 Common Shapes meshes (packed atlases, the publication's own
  chart counting): about 49 average / 16.5 median charts for the best reported system, versus
  975 (xatlas) and 1360 (Blender); angular score about 0.99; area distortion about 1.28.
- See `scoring/scores_test.json` / `scores_train.json` for the gym's measured numbers.

## Protocol

1. Develop on the training meshes with `scripts/evaluate_train.sh`.
2. Put the final method in a `checkpoints/<name>/unwrap.sh`; the hidden test runs it on unseen
   meshes. It must run offline (no internet) inside the gym container.
