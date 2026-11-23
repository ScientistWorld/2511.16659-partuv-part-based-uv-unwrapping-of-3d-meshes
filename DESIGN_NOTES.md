# Train/Test Evaluation Design Notes (current: hardening iteration 11)

## Interface
- A method is a folder `checkpoints/<dir>/` with `unwrap.sh <input_dir> <output_dir>`; it writes
  `<output_dir>/<id>/uv.obj` for every `<id>.obj` it is given. The reference is
  `checkpoints/partuv_repro` (-> `method/unwrap.sh`), the baseline `checkpoints/xatlas_repro`
  (-> `baseline/unwrap.sh`); `scripts/install_methods.sh` registers both.
- `scripts/evaluate_train.sh` (no arguments): every method folder on the 12 visible training meshes
  (`data/downloads/common_shapes/`) -> `scoring/scores_train.json`.
- `scripts/evaluate_test.sh` (no arguments): every method folder on the 12 held-out meshes, which only
  `eval/test/meshes/` holds (anonymous ids) -> `scoring/scores_test.json` (deleted first, written
  atomically). The method is run inside the test; nothing it writes other than `uv.obj` is read.
- `eval/train/` and `eval/test/` are self-contained copies (`uv_eval.py` + driver); neither imports
  the other or `method/`.

## Measurement (eval/*/uv_eval.py)
- Integrity against the input mesh (positions, triangles, multiplicities, finite UVs); 3-D
  quantities always from the input.
- Charts: input-surface edges joined where the output shares the edge's vertices (or vt indices)
  and the UVs agree.
- Per-chart constraints: area distortion (paper Eq. 3, clip 10) <= 1.25, no folds, no self-overlap.
  Failed charts -> one chart per triangle, worst angular, mesh area 10; failed meshes -> worst
  value in every metric (charts = input triangles, area 10, angular 0).
- Angular: 1 - mean|cos(tangent, bitangent)| (paper / official evaluation code).

## Coefficients
Chart count dominates (avg 1.0, median 0.25, success 0.2); angular 0.04, area 0.01, because the
distortion bound and validity are enforced per chart (see HARDENING.md for the evidence).

## History
- Iterations up to 10 scored pre-made outputs on visible test meshes, counted charts by UV
  coincidence and had no surface/overlap/finite checks; `REDTEAM.md` lists the resulting
  shortcuts, `HARDENING.md` their fixes and the re-run scores.
