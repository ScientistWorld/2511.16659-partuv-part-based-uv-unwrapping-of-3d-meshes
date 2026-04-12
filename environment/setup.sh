#!/bin/bash
# Container setup script: runs in an overlay at job runtime.
# Installs all Python packages needed for the PartUV reproduction.
# The overlay has the workspace mounted, so pip can write to the system Python.
set -e
export TMPDIR=/dev/shm
export UV_CACHE_DIR=/dev/shm/uv-cache
export UV_SYSTEM_PYTHON=1
export UV_BREAK_SYSTEM_PACKAGES=1

cd /home/user

# Install uv package manager
python3 -m pip install --no-cache-dir --break-system-packages uv 2>/dev/null || \
    pip install --no-cache-dir --break-system-packages uv 2>/dev/null || true

if ! command -v uv >/dev/null 2>&1; then
    python3 -m pip install --no-cache-dir --break-system-packages uv
fi

uv pip install --system -U pip setuptools wheel

# Install build tools
uv pip install --system cmake ninja scikit-build-core "pybind11[global]"

# PyTorch with CUDA 12.8 (torch keeps CUDA runtime in Python wheels)
uv pip install --system torch==2.7.1 --index-url https://download.pytorch.org/whl/cu128

# torch_scatter from prebuilt wheel
uv pip install --system /home/user/environment/wheels/torch_scatter-2.1.2+pt27cu128-cp312-cp312-linux_x86_64.whl

# Scientific Python stack
uv pip install --system \
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

# PartUV from prebuilt wheel
uv pip install --system /home/user/environment/wheels/partuv-0.1.2-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl

echo "Setup complete."
