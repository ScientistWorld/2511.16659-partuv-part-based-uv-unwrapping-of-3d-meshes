# Scientist Constraints

## Data
- **Development**: the 12 visible Common Shapes training meshes in `data/downloads/common_shapes/`
  (from `alecjacobson/common-3d-test-models`, fetched by `scripts/download.sh`).
- **Hidden test**: 12 other Common Shapes meshes held only by `eval/test/`. The method is run on
  them by `scripts/evaluate_test.sh`; it must not depend on knowing which meshes they are.

## Method interface
- A method is a folder `checkpoints/<name>/` with `unwrap.sh`, called as
  `bash unwrap.sh <input_dir> <output_dir>`; for every `<id>.obj` in the input it writes
  `<output_dir>/<id>/uv.obj` (OBJ with `v`, `vt`, `f v/vt` records).
- The output must keep the input surface: input vertex positions and input triangles (vertices
  may be duplicated along seams; quads may be split along either diagonal). Every corner needs a
  finite UV. Triangles of one chart must share vertex (or `vt`) indices along their common edges;
  coincident UVs on separate vertex copies do not join charts.
- It must run offline inside the gym container (no internet at test time) and finish; runtime is
  not scored.

## Fixed by the evaluator (not tunable by the method)
- The per-chart area-distortion threshold 1.25, the fold and self-overlap checks, the chart
  definition (input-surface edges joined by the output's shared vertices with equal UVs), the
  clipping at 10, the held-out meshes, and the worst values given to failed charts and failed
  meshes.

## Method scope
- The method must decompose meshes into charts and flatten them; packing alone does not change
  any scored metric.

## Out of Bounds
- Writing score files or numbers instead of UV OBJs (only `scripts/evaluate_*.sh` write scores).
- Changing `eval/`, `scripts/evaluate_*.sh`, the held-out meshes or the metric definitions.
- Detecting the held-out meshes by name/content to apply per-mesh hand-tuned settings.
- Proprietary or paid tools for the core method.

## Compliance Checklist
- [ ] Method folder with `unwrap.sh` under `checkpoints/`
- [ ] Every training mesh scored by `scripts/evaluate_train.sh` with success
- [ ] Charts within the 1.25 bound, no folds / overlaps
- [ ] No proprietary paid tools in the core algorithm
