# Reproduction Milestones

**Current: none**

## Progress Log

### [2026-04-12 17:40] - none
- Fixed container.def: added %files section to copy wheel files into container image at build time; merged all pip installs into %post
- Fixed wheel namespace packages: rebuilt partuv wheel with missing `__init__.py` for `partfield_official` package
- Fixed method/__init__.py: removed interfering relative imports
- Added missing __init__.py files to official_partuv source tree
- Fixed baseline.sh, method.sh, reproduce.sh: corrected output path mismatches
- Fixed official_pipeline.py: corrected wheel import paths
- Updated run.sh: proper resource verification and limit support
- Committed all fixes (git commit 5d701ce)
- Submitting GPU job to run PartUV on Common Shapes dataset (24 meshes)
