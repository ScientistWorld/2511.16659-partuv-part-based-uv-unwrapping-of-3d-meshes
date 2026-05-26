# Scientist Constraints

## Data
The scientist must evaluate on the provided Common Shapes benchmark:
- **Common Shapes**: meshes from `alecjacobson/common-3d-test-models`, populated by `scripts/download.sh` under `/home/user/data/downloads/common_shapes`

Additional datasets may be added later, but any claimed improvement over the current reproduction must include the same Common Shapes evaluation.

## Method
The scientist must stay within the UV unwrapping problem setting:
- The method must output UV coordinates for each input mesh
- The method must explicitly address chart decomposition rather than only UV packing
- Improvements must preserve the chart-count vs distortion tradeoff measured in `scoring/reference.json`
- The method must operate on mesh geometry and output real UV-mapped mesh artifacts that `scripts/evaluate.sh` can score

## Out of Bounds
- Returning score files or chart counts without producing corresponding UV OBJ outputs
- Evaluating on a different mesh set without also reporting Common Shapes
- Changing the metric definitions in `scripts/evaluate.sh` / `eval/`
- Using proprietary or paid tools for the core method

## Compliance Checklist
- [ ] Evaluation conducted on Common Shapes dataset (or equivalent meshes)
- [ ] UV unwrapping method decomposes meshes into charts and assigns UV coordinates
- [ ] Report all scored Common Shapes metrics: success rate, chart counts, angular distortion, and area distortion
- [ ] Seam length and overall atlas area may be logged as diagnostics, but are not scored in this gym because packing is not standardized
- [ ] Runtime may be logged for diagnostics, but wall-clock speed is not a scored optimization target
- [ ] No proprietary paid tools used for core algorithm
