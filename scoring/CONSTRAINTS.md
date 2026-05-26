# Scientist Constraints

## Data
The scientist must evaluate on the provided Common Shapes benchmark:
- **Common Shapes**: meshes from `alecjacobson/common-3d-test-models`, populated by `scripts/download.sh` under `/home/user/data/downloads/common_shapes`

Additional datasets may be added later, but any claimed improvement over the current reproduction must include the same Common Shapes evaluation.

## Method
The scientist must stay within the PartUV problem setting:
- The method must output UV coordinates for each input mesh
- The method must explicitly address chart decomposition rather than only UV packing
- Improvements must preserve the chart-count vs distortion tradeoff measured in `scoring/reference.json`
- A learned part prior is allowed, but a pure surrogate that bypasses the decomposition/search structure is out of scope for comparing against this environment

## Out of Bounds
- Replacing the decomposition-and-search pipeline with a generic end-to-end surrogate
- Evaluating on a different mesh set without also reporting Common Shapes
- Changing the metric definitions in `scripts/evaluate.sh` / `eval/`
- Using proprietary or paid tools for the core method

## Compliance Checklist
- [ ] Evaluation conducted on Common Shapes dataset (or equivalent meshes)
- [ ] UV unwrapping method decomposes meshes into charts and assigns UV coordinates
- [ ] Report all scored Common Shapes metrics: success rate, chart counts, angular distortion, and area distortion
- [ ] Seam length and overall atlas area may be logged as diagnostics, but are not scored in this gym because the released PartUV export is not the paper's final packed atlas
- [ ] Runtime may be logged for diagnostics, but wall-clock speed is not a scored optimization target
- [ ] No proprietary paid tools used for core algorithm
