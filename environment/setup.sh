#!/bin/bash
# Container setup script: installs Python packages.
set -e
export TMPDIR=/dev/shm

cd /home/user

PIP="/opt/venv/bin/pip"

$PIP install -U pip wheel

# CPU-only PyTorch (much faster to download than CUDA version)
$PIP install torch==2.7.1 --index-url https://download.pytorch.org/whl/cpu

# torch_scatter CPU for cp312
$PIP install https://data.pyg.org/whl/torch-2.7.0+cpu/torch_scatter-2.1.2+pt27cpu-cp312-cp312-linux_x86_64.whl

# PartUV and dependencies
$PIP install partuv==0.1.2 trimesh==4.9.0 xatlas scipy opencv-python libigl

# PartField dependencies
$PIP install einops lightning loguru meshio plyfile pyyaml tqdm numpy

echo "Setup complete."
