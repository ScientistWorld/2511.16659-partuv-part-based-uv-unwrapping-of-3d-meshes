# Evaluation Targets

## Experiment: common_shapes_comparison
Compare UV unwrapping methods on Common Shapes meshes (12 visible training meshes; 12 held-out
meshes for the hidden test) with the quantities of the paper's Table 1, under the paper's fixed
per-chart distortion threshold (tau = 1.25).

## Primary: chart_count_reduction
Sharply fewer charts than standard UV unwrapping tools.
- **Metrics**: `avg_charts`, `median_charts` (lower is better)
- **How measured**: charts are connected sets of input triangles joined along input edges where the
  output shares the edge's vertices (or vt indices) with equal UVs; a chart that fails a
  constraint below counts as one chart per triangle; a failed mesh counts one chart per input
  triangle.
- **Reference (hidden test)**: see `scores_test.json` entry `partuv`; baseline `xatlas`.

## Constraint: bounded_distortion
Fewer charts must not be bought with distortion.
- **Hard bound**: every chart's area distortion (paper Eq. 3, triangle values clipped at 10)
  must be <= 1.25; otherwise the chart is failed (one chart per triangle, mesh area
  distortion 10, worst angular value for its triangles).
- **Metrics**: `area_distortion` (lower; mean over meshes of the worst chart), `angular_distortion`
  (higher; 1 - mean |cos(tangent, bitangent)|, paper Sec. 4.1).

## Constraint: valid_parameterization
Charts must be usable texture charts and cover the input.
- **Hard checks**: no folded interior edge, no self-overlap within a chart, the output keeps the
  input's vertex positions and triangles, finite UVs. Fold/overlap failures fail the chart;
  surface or UV failures fail the mesh (worst value in every metric).

## Constraint: reliability
- **Metric**: `success_rate` (higher): % of meshes with intact output and only valid charts.

## Not scored
- Seam length and overall atlas area distortion (need a standardised packing stage).
- Runtime (hardware dependent).
