# Overview

- **Paper ID:** 2511.16659
- **Title:** PartUV: Part-Based UV Unwrapping of 3D Meshes
- **Domain:** Computer Graphics / 3D Geometry Processing
- **TL;DR:** PartUV uses learning-based part decomposition combined with geometry-based heuristics and recursive search to produce UV unwrappings with significantly fewer charts than existing tools, while maintaining low distortion and part-aligned boundaries.

## Short Summary

UV unwrapping flattens 3D meshes onto 2D planes for texture mapping. Existing methods (xatlas, Blender) often produce highly fragmented charts on complex meshes. PartUV introduces a two-stage approach: first uses PartField (a learning-based method) for semantic part decomposition, then applies two geometry-based heuristics (Normal clustering and OBB-based Merge) in a top-down recursive search with ABF++ flattening. The result is fewer charts with boundaries aligned to meaningful object parts, while keeping distortion low.

## Key Results

- On Common Shapes (24 meshes): PartUV produces 48.6 average charts vs 974.8 (xatlas) and 1360.3 (Blender) — a 20x-28x reduction
- On Trellis (114 AI-generated meshes): 568.7 average charts vs 1541.6 (xatlas) — 2.7x reduction
- On PartObjaverseTiny (200 man-made meshes): 544.8 average charts vs 1142.1 (xatlas) — 2.1x reduction
- Angular distortion remains high (~0.98) across datasets, comparable to baselines
- 100% success rate across all four datasets
- Runtime: typically a few to tens of seconds per mesh

---

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

---

# Paper's Method

How the paper approaches the problem, i.e. the paper's core contributions.

## Key Contribution

PartUV introduces a **part-based UV unwrapping pipeline** that combines semantic part decomposition (via a learning-based method called PartField) with geometry-based heuristics in a top-down recursive tree search. The key insight is that leveraging high-level semantic priors for mesh decomposition — rather than relying solely on local geometric properties — yields significantly fewer, part-aligned charts while maintaining low distortion.

## Approach

1. **Hierarchical Part Tree Construction**: Given a 3D mesh, the method first uses a learning-based feature field (PartField) to predict per-face part features. Agglomerative clustering on these features builds a hierarchical binary tree where leaf nodes are individual faces and the root encompasses the entire mesh.

2. **Top-Down Recursive Tree Search**: The algorithm recursively traverses the part tree. For each node (a submesh), it applies two geometry-based heuristics to decompose the submesh into charts:
   - **Normal Heuristic**: Agglomerative clustering of face normals produces 1 to 10 candidate chart decompositions. Each candidate is flattened via ABF++ and evaluated for distortion.
   - **Merge Heuristic**: For each part, computes an oriented bounding box (OBB), assigns each face to one of 6 OBB faces, segments by connectivity, then iteratively merges adjacent components if distortion stays below threshold.

3. **ABF++ Flattening**: Each candidate chart is flattened using Angle-Based Flattening (ABF++), which optimizes triangle angles to minimize conformal distortion.

4. **Distortion Threshold**: The search ensures each chart's distortion stays below a user-specified threshold τ (default 1.25) while minimizing total chart count.

5. **UV Packing**: Final charts are packed into the [0,1]×[0,1] UV atlas space using UVPackMaster.

## Main Claims

1. **Primary**: PartUV generates significantly fewer charts (1/3 to 1/31 compared to baselines) with boundaries aligned to semantic parts, while maintaining comparable or better distortion.
2. **Secondary**: PartUV maintains low distortion (angular ~0.98-0.99, area ~1.1-1.4) comparable to or better than baselines.
3. **Tertiary**: PartUV achieves 100% success rate on diverse datasets (man-made, CAD, AI-generated) and runs in typically a few to tens of seconds per mesh.

---

# Evaluation

How success is measured. Describe only the metrics, targets, and evaluation procedure — do NOT describe the paper's method or how they achieved these results. Think of this as a general evaluation protocol for other scientists trying to solve the same problem, where they should not see this paper's solution.

## Metrics

Four metrics are used to evaluate UV unwrapping quality:

1. **Number of Charts** — Count of disconnected UV chart regions covering the mesh. Lower is better. Both average and median across the dataset are reported.
2. **Seam Length** — Sum of lengths of all chart boundary edges, with UV coordinates normalized to a [0,1] grid. Lower is better; median across the dataset is reported.
3. **Angular (Conformal) Distortion** — Computed as one minus the average cosine between tangent and bitangent vectors of each face. Closer to 1.0 is better (1.0 = perfect angle preservation). Average across the dataset is reported.
4. **Area (Equiareal) Distortion** — Ratio of 2D chart area to 3D surface area per face, clipped to a maximum of 10. Lower is better. Two variants: (a) "area distortion" — the worst chart in each shape (max across charts), averaged across dataset; (b) "overall area distortion" — average across all faces in all charts.
5. **Success Rate** — Percentage of meshes successfully processed without timeout or error.

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
3. Compute all four metrics for each mesh
4. Aggregate metrics across the dataset: average and median chart count, median seam length, average distortions, success rate
5. For primary comparison, focus on chart count (lower is better) while maintaining distortion below acceptable thresholds

---

# Reproduction Milestones

**Current: method_runs**

## Progress Log

### [2026-04-04] - none
- Read the PartUV paper (2511.16659)
- Identified core components: PartField part decomposition, Normal/Merge heuristics, ABF++ flattening, top-down recursive search
- Analyzed paper's key claims: 2-30x fewer charts than baselines, low distortion, 100% success rate

### [2026-04-04] - method_runs
- Implemented full PartUV pipeline in Python
- Implemented LSCM flattening (ABF++ alternative) for chart parameterization
- Implemented Normal heuristic (agglomerative clustering of face normals)
- Implemented Merge heuristic (OBB-based merging)
- Implemented hierarchical part tree with recursive search (Algorithm 1)
- Implemented xatlas baseline (with fallback to geometric clustering)
- Implemented evaluation metrics (chart count, seam length, angular/area distortion)
- Created data loading for Common Shapes dataset
- Created all shell scripts (download, evaluate, reproduce, run, method, baseline)
- Environment setup: numpy, scipy, scikit-learn, trimesh, meshio, xatlas, tqdm, pandas
- Common Shapes dataset downloaded (22 meshes from GitHub)
- Submitted full reproduction job (xatlas + PartUV on all meshes)

## Stop Justification

<!-- Do not edit this unless you decide to stop -->
