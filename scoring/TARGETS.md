# Evaluation Targets

## Experiment: common_shapes_comparison
Compare UV unwrapping methods on the Common Shapes benchmark using the metrics reported in Table 1 of the paper.

## Primary: chart_count_reduction
PartUV's main claim is that it sharply reduces chart fragmentation relative to Blender and xatlas.
- **Metrics**: `avg_charts`, `median_charts` (lower is better)
- **Direction**: Lower is better
- **How to run**: Run a UV unwrapping method on the Common Shapes meshes, infer connected UV charts from the exported UV OBJ, and aggregate per-mesh chart counts

## Constraint: bounded_distortion
The chart reduction must not be purchased by excessive distortion.
- **Metrics**: `angular_distortion` (higher is better), `area_distortion` (lower is better), `overall_area_distortion` (lower is better)
- **Direction**: Match or approach the paper's distortion regime while reducing charts
- **How to run**: Compute the distortion metrics from the UV-mapped OBJ outputs produced by each method

## Constraint: seam_length
The paper also reports seam length as part of the quality tradeoff.
- **Metric**: `seam_length` (lower is better)
- **Direction**: Lower is better
- **How to run**: Sum UV boundary edge lengths from the exported UV OBJ

## Constraint: reliability_and_speed
The method should finish successfully on the benchmark and remain reasonably fast.
- **Metrics**: `success_rate` (higher is better), `avg_time` (lower is better)
- **Direction**: Higher success rate and lower runtime are better
- **How to run**: Record per-mesh success/failure and wall-clock runtime during method execution
