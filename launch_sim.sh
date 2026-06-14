#!/usr/bin/env bash
set -eo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Use CycloneDDS with increased participant limits for multi-robot setup
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI="file://${ROOT_DIR}/config/cyclonedds.xml"

# Clean DDS state from previous runs
rm -rf /tmp/firescout_models 2>/dev/null || true

# Source ROS 2
source /opt/ros/kilted/setup.bash

# Build and source
cd "$ROOT_DIR"
colcon build \
    --cmake-clean-cache \
    --cmake-args \
        -DPython3_EXECUTABLE=/usr/bin/python3 \
        -DPYTHON_EXECUTABLE=/usr/bin/python3

source install/setup.bash

echo "=== Launching Fire-Scout full system with CycloneDDS ==="
echo "RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION}"
echo "CYCLONEDDS_URI=${CYCLONEDDS_URI}"

ros2 launch bringup full_system.launch.py \
    simulation:=true \
    use_sim_time:=true \
    world_name:=villa_world \
    enable_nav2:=false \
    enable_fire_suppression:=true \
    launch_profile:=sim
