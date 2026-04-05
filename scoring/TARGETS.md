# Evaluation Targets

## Primary: chart_count_reduction
Reduce the number of UV charts compared to baseline methods (xatlas, Blender) on 3D mesh datasets, while maintaining low distortion. PartUV claims 2-30x fewer charts depending on dataset.
- **Metric**: avg_charts (lower is better)
- **Direction**: Lower is better — fewer charts means less fragmentation, fewer seams, better downstream usability
- **How to run**: Run UV unwrapping method on meshes, count number of chart regions, average across dataset

## Constraint: distortion_bounded
Area distortion must remain below ~1.4 (1.0 is perfect). PartUV's value proposition is reducing chart count WITHOUT sacrificing distortion.
- **Metric**: area_distortion (lower is better)
- **Direction**: Must be ≤ 1.4 to be competitive; significantly higher means the method is cutting corners
- **How to run**: Compute area stretch per triangle face after UV mapping, aggregate per-chart and per-shape

## Constraint: angular_preservation
Angular distortion should remain high (~0.98+). This measures how well angles are preserved during flattening.
- **Metric**: angular_distortion (higher is better, measured as 1 - avg_cosine)
- **Direction**: Higher (closer to 1.0) is better
- **How to run**: Compute tangent/bitangent vectors per face, measure cosine between them

## Secondary: seam_length
Total seam length should be minimized. Shorter seams mean fewer visible artifacts.
- **Metric**: median_seam_length (lower is better)
- **Direction**: Lower is better
- **How to run**: Sum lengths of all chart boundary edges in normalized UV space

## Secondary: success_rate
Method should successfully process all meshes without timeout or error.
- **Metric**: success_rate (higher is better)
- **Direction**: Higher is better; 100% is the target
- **How to run**: Count successful runs vs total meshes

## Secondary: runtime
Method should complete within reasonable time (typically under 1 minute per mesh).
- **Metric**: time_seconds (lower is better)
- **Direction**: Lower is better
- **How to run**: Time each mesh processing, report average
