#!/usr/bin/env bash
set -eo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "$#" -gt 0 ]]; then
	PKG_ARGS=(--packages-select "$@")
else
	PKG_ARGS=()
fi

# Force system Python/ROS tooling even if a venv or conda env is active.
unset VIRTUAL_ENV
unset CONDA_PREFIX
unset PYTHONHOME
unset PYTHONPATH
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/opt/ros/kilted/bin"

source /opt/ros/kilted/setup.bash
cd "$ROOT_DIR"

colcon build \
	--cmake-clean-cache \
	--cmake-args \
		-DPython3_EXECUTABLE=/usr/bin/python3 \
		-DPYTHON_EXECUTABLE=/usr/bin/python3 \
	"${PKG_ARGS[@]}"
source install/setup.bash
colcon test "${PKG_ARGS[@]}"
colcon test-result --all --verbose
