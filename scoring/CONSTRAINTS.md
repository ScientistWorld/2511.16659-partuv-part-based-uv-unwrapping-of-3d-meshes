# Scientist Constraints

## Data
The scientist must use the provided datasets for evaluation:
- **Common Shapes**: 24 meshes from `alecjacobson/common-3d-test-models` (GitHub). These are the primary benchmark.
- The system may include additional datasets (Trellis, ABC, PartObjaverseTiny) if accessible.

No external 3D mesh datasets may be used. The evaluation must be conducted on the same test meshes used to establish the baseline.

## Method
The scientist must work within the **mesh decomposition and UV unwrapping** problem space. Specifically:
- The method must produce UV coordinates and chart assignments for input 3D meshes
- The core algorithmic contribution must involve **mesh decomposition into charts** — not just post-processing or packing improvements alone
- Using a pretrained part segmentation model is allowed and encouraged (e.g., PartField if available)
- Using geometric features (normals, curvature, etc.) for decomposition is allowed
- The distortion threshold mechanism (keeping distortion bounded) is a key design element

## Out of Bounds
- Switching to fundamentally different UV mapping paradigms (e.g., neural field optimization per mesh) that take >5 minutes per mesh. The paper emphasizes speed as a feature.
- Using proprietary or paid tools for the core algorithm (the scientist must use open-source or self-implemented methods)
- Changing the metric definitions (angular distortion = 1 - avg_cosine, area distortion from stretch ratio)

## Compliance Checklist
- [ ] Evaluation conducted on Common Shapes dataset (or equivalent meshes)
- [ ] UV unwrapping method decomposes meshes into charts and assigns UV coordinates
- [ ] All five metrics are computed (chart count, seam length, angular distortion, area distortion, success rate)
- [ ] Runtime per mesh is under 5 minutes (preferably under 1 minute)
- [ ] No proprietary paid tools used for core algorithm
