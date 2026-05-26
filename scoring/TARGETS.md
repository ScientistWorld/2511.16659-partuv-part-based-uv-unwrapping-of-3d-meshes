# Evaluation Targets

## Experiment: common_shapes_comparison
Compare UV unwrapping methods on the Common Shapes benchmark using the metrics reported in Table 1 of the paper.

## Primary: chart_count_reduction
The main target is sharply reducing chart fragmentation relative to standard UV unwrapping baselines.
- **Metrics**: `avg_charts`, `median_charts` (lower is better)
- **Direction**: Lower is better
- **How to run**: Run a UV unwrapping method on the Common Shapes meshes, infer connected UV charts from the exported UV OBJ, and aggregate per-mesh chart counts

## Constraint: bounded_distortion
The chart reduction must not be purchased by excessive distortion.
- **Metrics**: `angular_distortion` (higher is better), `area_distortion` (lower is better)
- **Direction**: Match or approach the paper's distortion regime while reducing charts
- **How to run**: Compute the distortion metrics from the UV-mapped OBJ outputs produced by each method

## Constraint: reliability
The method should finish successfully on the benchmark.
- **Metric**: `success_rate` (higher is better)
- **Direction**: Higher success rate is better
- **How to run**: Record per-mesh success/failure during method execution
- **Scoring**: This is a low-weight constraint metric in `scoring/reference.json`, so methods that fail on difficult meshes are penalized even if their successful outputs have few charts.

## Diagnostic: packing-dependent metrics
The paper reports seam length and overall area distortion after atlas packing.
The current reproduction artifacts expose chart components before a standardized
packing pass, so this gym logs `seam_length` and `overall_area_distortion` in
per-run artifacts but does not score them.

## Diagnostic: runtime
The paper reports runtime, but this gym does not score wall-clock time because
hardware varies across runs. Per-mesh runtimes may still be logged in method
artifacts for debugging and rough comparison.
