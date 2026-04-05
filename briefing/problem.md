# Problem Definition

What problem does this paper address? Write this so that someone with no knowledge of the paper can understand what needs to be solved and how success is measured.

Do NOT describe the paper's method or solution here — only the problem itself. Think about if a future scientist agent try to solve this problem from scratch without knowing what approach the paper took. If you leak the solution, you compromise the benchmark.

## Research Question

UV unwrapping projects 3D mesh surfaces onto 2D planes by assigning every 3D surface point a corresponding 2D UV coordinate. For complex meshes, flattening the entire surface into a single 2D chart introduces large distortion. Chart segmentation (seam cutting) divides the mesh into multiple charts, each flattened separately, but existing methods often produce highly fragmented charts — a single chart may contain only one or a handful of triangles — which hampers texture painting, introduces artifacts at chart boundaries, and burdens downstream applications.

## Why It Matters

AI-generated meshes (extracted from neural fields via marching cubes) are typically noisy, bumpy, and geometrically poor. Existing UV unwrapping tools tuned for well-behaved artist-created meshes often fail on these — producing extreme fragmentation, timing out, or yielding unintuitive seam placements. Better UV unwrapping enables downstream 3D content creation with fewer artifacts, shorter seams, and charts aligned with meaningful object parts.

## Success Criteria

A successful solution should produce UV mappings with:
1. **Fewer charts** — a significantly smaller number of charts than existing tools (baseline: xatlas, Blender)
2. **Low distortion** — angular (conformal) distortion and area (equiareal) distortion comparable to or better than baselines
3. **Shorter seams** — total seam length should be minimized, as longer seams introduce more visible artifacts
4. **Part-aligned boundaries** — chart boundaries should align with meaningful object parts (e.g., not cut across a flat surface like a TV screen)
5. **Robust and fast** — should succeed on diverse mesh types (man-made, CAD, AI-generated) within reasonable time (typically a few to tens of seconds)
