#!/bin/bash
set -e
export TMPDIR=/dev/shm
export UV_CACHE_DIR=/dev/shm/uv-cache

cd /home/user

uv pip install --system -U pip setuptools wheel
uv pip install --system cmake ninja scikit-build-core "pybind11[global]"

# Official PartUV release targets Torch 2.7.1 with CUDA 12.8 wheels.
uv pip install --system torch==2.7.1 --index-url https://download.pytorch.org/whl/cu128
uv pip install --system torch-scatter -f https://data.pyg.org/whl/torch-2.7.1+cu128.html

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

uv pip install --system --no-build-isolation -e /home/user/method/official_partuv
