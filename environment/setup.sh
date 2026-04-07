#!/bin/bash
set -e
export TMPDIR=/dev/shm
export UV_CACHE_DIR=/dev/shm/uv-cache

cd /home/user

uv pip install --system -U pip setuptools wheel
uv pip install --system cmake ninja scikit-build-core "pybind11[global]"

# Use prebuilt wheels where available to avoid compiling PartUV from source.
# Torch keeps the CUDA 12.8 runtime in Python wheels, so the base image does
# not need to provide a CUDA toolkit.
uv pip install --system torch==2.7.1 --index-url https://download.pytorch.org/whl/cu128
uv pip install --system /home/user/environment/wheels/torch_scatter-2.1.2+pt27cu128-cp312-cp312-linux_x86_64.whl

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

uv pip install --system /home/user/environment/wheels/partuv-0.1.2-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl
