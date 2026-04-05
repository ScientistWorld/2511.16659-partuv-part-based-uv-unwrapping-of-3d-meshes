#!/bin/bash
# Install Python packages into the container overlay.
#
# IMPORTANT: Use TMPDIR=/dev/shm because /tmp is a 64MB tmpfs that fills up.
set -e
export TMPDIR=/dev/shm
export UV_CACHE_DIR=/dev/shm/uv-cache

cd /home/user

# Core scientific computing
pip install numpy scipy scikit-learn

# Mesh processing
pip install trimesh meshio

# xatlas for UV unwrapping baseline
pip install xatlas

# Progress bars
pip install tqdm pandas

echo "Environment setup complete"
