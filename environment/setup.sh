#!/bin/bash
# Container setup script: installs all Python packages.
# Runs in overlay at job runtime.
# IMPORTANT: Call venv pip directly to avoid fakeroot issues.
set -e
export TMPDIR=/dev/shm

cd /home/user

PIP="/opt/venv/bin/pip"

$PIP install -U pip wheel

$PIP install cmake ninja scikit-build-core pybind11-global

$PIP install torch==2.7.1 -i https://download.pytorch.org/whl/cu128

$PIP install https://data.pyg.org/whl/torch-2.7.0+cu128/torch_scatter-2.1.2+pt27cu128-cp312-cp312-linux_x86_64.whl

$PIP install \
    boto3 einops h5py libigl lightning loguru meshio open3d opencv-python \
    pandas plyfile pyyaml scikit-image scikit-learn seaborn tqdm trimesh xatlas yacs

$PIP install partuv==0.1.2

echo "Setup complete."
