#!/bin/bash
# Container setup script: installs all Python packages.
# Runs in overlay at job runtime (not under fakeroot) with full network access.
# Uses Python 3.12 from the base container's venv.
set -e
export TMPDIR=/dev/shm
export UV_CACHE_DIR=/dev/shm/uv-cache
export UV_SYSTEM_PYTHON=1
export UV_BREAK_SYSTEM_PACKAGES=1

cd /home/user

# Use the venv Python 3.12
PIP="/opt/venv/bin/pip"

# Upgrade pip
$PIP install --no-cache-dir -U pip wheel

# Build tools
$PIP install --no-cache-dir cmake ninja scikit-build-core "pybind11[global]"

# PyTorch with CUDA 12.8
$PIP install --no-cache-dir torch==2.7.1 --index-url https://download.pytorch.org/whl/cu128

# torch_scatter from PyG wheel index (cu128, cp312 for Python 3.12)
$PIP install --no-cache-dir \
    https://data.pyg.org/whl/torch-2.7.0+cu128/torch_scatter-2.1.2+pt27cu128-cp312-cp312-linux_x86_64.whl

# Scientific Python stack
$PIP install --no-cache-dir \
    boto3 \
    h5py \
    libigl \
    lightning==2.2 \
    loguru \
    meshio \
    open3d \
    opencv-python \
    pandas \
    plyfile \
    pyyaml \
    scikit-image \
    scikit-learn \
    seaborn \
    tqdm \
    trimesh==4.9.0 \
    xatlas \
    yacs \
    einops

# PartUV from PyPI
$PIP install --no-cache-dir partuv==0.1.2

echo "Setup complete."
