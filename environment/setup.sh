#!/bin/bash
# Container setup script: installs Python packages.
set -e
export TMPDIR=/dev/shm
export MPLCONFIGDIR=/dev/shm/matplotlib

cd /home/user

export UV_SYSTEM_PYTHON=1
export UV_BREAK_SYSTEM_PACKAGES=1

uv pip install --system -U pip wheel

# NumPy is pinned to a conservative Python 3.12 wheel. Newer NumPy 2.4 wheels
# have crashed during import on the one-CPU compute test image before any
# Python traceback could be emitted.
uv pip install --system "numpy==1.26.4"

# PyTorch. Prefer the staged CUDA wheel when present so compute nodes do not
# rely on runtime downloads.
if [ -f /home/user/environment/wheels/torch-2.7.1+cu128-cp312-cp312-manylinux_2_28_x86_64.whl ]; then
  uv pip install --system /home/user/environment/wheels/torch-2.7.1+cu128-cp312-cp312-manylinux_2_28_x86_64.whl
else
  uv pip install --system torch==2.7.1 --index-url https://download.pytorch.org/whl/cpu
fi

if [ -f /home/user/environment/wheels/torch_scatter-2.1.2+pt27cu128-cp312-cp312-linux_x86_64.whl ]; then
  uv pip install --system /home/user/environment/wheels/torch_scatter-2.1.2+pt27cu128-cp312-cp312-linux_x86_64.whl
else
  uv pip install --system https://data.pyg.org/whl/torch-2.7.0+cpu/torch_scatter-2.1.2+pt27cpu-cp312-cp312-linux_x86_64.whl
fi

# Core dependencies
uv pip install --system partuv==0.1.2 trimesh==4.9.0 xatlas scipy "opencv-python==4.11.0.86" libigl einops lightning loguru meshio plyfile pyyaml tqdm "numpy==1.26.4"

# PartField / partuv transitive dependencies
uv pip install --system scikit-learn scikit-image h5py boto3 psutil pytz matplotlib pillow imageio kornia yacs seaborn open3d "numpy==1.26.4"

echo "Setup complete."
