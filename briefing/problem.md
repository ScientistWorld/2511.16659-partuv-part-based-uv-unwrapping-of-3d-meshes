# Problem Definition

## Research Question

UV unwrapping projects 3D mesh surfaces onto 2D planes by assigning every 3D surface point a corresponding 2D UV coordinate. For complex meshes, flattening the entire surface into a single 2D chart introduces large distortion. Chart segmentation (seam cutting) divides the mesh into multiple charts, each flattened separately, but existing methods often produce highly fragmented charts — a single chart may contain only one or a handful of triangles — which hampers texture painting, introduces artifacts at chart boundaries, and burdens downstream applications.

## Why It Matters

AI-generated meshes (extracted from neural fields via marching cubes) are typically noisy, bumpy, and geometrically poor. Existing UV unwrapping tools tuned for well-behaved artist-created meshes often fail on these — producing extreme fragmentation, timing out, or yielding unintuitive seam placements. Better UV unwrapping enables downstream 3D content creation with fewer artifacts, shorter seams, and charts aligned with meaningful object parts.

## Problem as posed in this gym

Given a triangle mesh, assign a UV coordinate to every face corner so that the surface is cut
into as few charts as possible, where every chart

- is a connected set of the input's triangles, mapped continuously (shared edges keep shared UVs),
- is injective in UV (no folded triangles, no self-overlap), and
- has area distortion at most a fixed threshold of 1.25 (mean over the chart's triangles of
  max(s, 1/s), s = a triangle's UV-to-3-D area ratio relative to its chart's ratio).

The input surface must be kept as is. Angular (conformal) distortion should stay low. The
threshold is part of the problem, not a tuning knob: a chart above it is a failed chart.
Evaluation is on unseen meshes (see `evaluation.md`).

## Success Criteria

A successful solution should produce UV mappings with:
1. **Fewer charts** — a significantly smaller number of charts than existing tools (baseline: xatlas, Blender)
2. **Bounded distortion** — every chart within the 1.25 area-distortion bound, with angular (conformal) distortion comparable to or better than baselines
3. **Valid charts** — no folded or self-overlapping charts, and the full input surface covered
4. **Coherent boundaries** — chart boundaries should follow visually and geometrically sensible regions rather than cutting arbitrarily across simple surfaces (not scored)
5. **Robust** — should succeed on every mesh, including large and multi-component ones; runtime matters in practice but is not scored here
