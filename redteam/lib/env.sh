# Shared environment for red-team runs (sourced by every redteam/<name>/run.sh).
# Mirrors the thread/env settings of scripts/method.sh so method runs behave the same.
export TMPDIR=/dev/shm
export PYTHONFAULTHANDLER=1
export PYTHONNOUSERSITE=1
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export OPENBLAS_CORETYPE="${OPENBLAS_CORETYPE:-GENERIC}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"
export NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}"
export MPLCONFIGDIR=/dev/shm/matplotlib

RT=/home/user/redteam
# Every scenario writes its method outputs under its own checkpoint root, as an agent
# would under checkpoints/, so scenarios never touch the reference outputs.
ROOT="/home/user/checkpoints/rt/${NAME}"
REF_OUT=/home/user/checkpoints/partuv_repro
DATA_DIR=/home/user/data/downloads/common_shapes

# The held-out slice is visible to any agent: it is every Common Shapes OBJ that is not
# in the train list of eval/train/evaluate_uv_outputs.py. Only these meshes enter the
# hidden test, so method outputs are generated for them; one train mesh ("woody", 13 s)
# is added so that scripts/evaluate_train.sh discovers and registers the output folder.
TEST_MESHES="alligator armadillo beetle-alt cow happy horse lucy nefertiti rocker-arm stanford-bunny teapot xyzrgb_dragon"
REGISTER_MESH="woody"
RUN_MESHES="$TEST_MESHES $REGISTER_MESH"
