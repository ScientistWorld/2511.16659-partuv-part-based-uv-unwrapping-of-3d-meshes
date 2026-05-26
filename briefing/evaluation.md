# Evaluation

How success is measured. Describe only the metrics, targets, and evaluation procedure — do NOT describe the paper's method or how they achieved these results. Think of this as a general evaluation protocol for other scientists trying to solve the same problem, where they should not see this paper's solution.

## Metrics

The paper reports the following UV unwrapping metrics:

1. **Number of Charts** — Count of disconnected UV chart regions covering the mesh. Lower is better. Both average and median across the dataset are reported.
2. **Seam Length** — Sum of lengths of all chart boundary edges, with UV coordinates normalized to a [0,1] grid. Lower is better; aggregate consistently across the dataset using the same convention as the chosen benchmark table.
3. **Angular (Conformal) Distortion** — Computed as one minus the average cosine between tangent and bitangent vectors of each face. Closer to 1.0 is better (1.0 = perfect angle preservation). Average across the dataset is reported.
4. **Area (Equiareal) Distortion** — Ratio of 2D chart area to 3D surface area per face, clipped to a maximum of 10. Lower is better. Two variants: (a) "area distortion" — the worst chart in each shape (max across charts), averaged across dataset; (b) "overall area distortion" — average across all faces in all charts.
5. **Success Rate** — Percentage of meshes successfully processed without timeout or error.

This gym scores chart count, success rate, angular distortion, and chart-level area distortion. Seam length and overall atlas area distortion are retained as diagnostics in per-run JSON artifacts because they depend on the final atlas packing stage and require a consistently packed atlas output.

## Baselines and Targets

The paper compares against several widely-used UV unwrapping tools:
- **Blender Smart UV Project** — clusters triangles by normals, projects onto planes
- **xatlas** — greedy chart growing with LSCM flattening
- **Open3D** — region growing with LSCM flattening
- **Nuvo** — neural field-based UV mapping (optimization-based)
- **OptCuts** — joint cut and parameterization optimization

Target levels (from the paper, approximate ranges):
- Chart count: PartUV achieves 1/3 to 1/31 fewer charts than Blender/xatlas
- Angular distortion: ~0.98-0.99 (near 1.0 is best)
- Area distortion: ~1.1-1.4 (near 1.0 is best)
- Success rate: 100% for PartUV, lower for some baselines

## Evaluation Protocol

1. Load each mesh from the test dataset
2. Run the UV unwrapping method to generate UV coordinates and chart assignments
3. Compute chart counts, success rate, and distortion metrics for each mesh
4. Aggregate metrics across the dataset: average and median chart count, average distortions, and success rate using the same aggregation convention throughout the benchmark
5. For primary comparison, focus on chart count (lower is better) while maintaining distortion below acceptable thresholds

Runtime may be logged as diagnostic metadata, but it is not a scored metric in
this reusable gym because wall-clock measurements vary with hardware.
