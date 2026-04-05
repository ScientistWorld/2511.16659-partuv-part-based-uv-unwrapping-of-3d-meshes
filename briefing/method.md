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
