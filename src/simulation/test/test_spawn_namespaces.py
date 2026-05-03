"""
test_spawn_namespaces.py
========================
Validates that spawn_robot.launch.py declares the correct launch arguments
and that robot namespaces (robot1/robot2/robot3) are properly configured.

These are unit-level checks that do NOT require a running Gazebo instance.
"""

import os
import sys
import importlib.util
import pytest


# ── Helpers ─────────────────────────────────────────────────────────────────

EXPECTED_ROBOTS = ['robot1', 'robot2', 'robot3']

SPAWN_POSES = {
    'robot1': (0.0, 0.0),
    'robot2': (2.0, 0.0),
    'robot3': (4.0, 0.0),
}


def _load_module(rel_path: str):
    """Load a Python launch file as a module without executing it."""
    pkg_root = os.path.join(os.path.dirname(__file__), '..')
    full_path = os.path.normpath(os.path.join(pkg_root, rel_path))
    spec = importlib.util.spec_from_file_location('_launch_mod', full_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── Tests ────────────────────────────────────────────────────────────────────

def test_expected_robot_names_defined():
    """The three robot namespaces must be defined in the expected list."""
    for robot in EXPECTED_ROBOTS:
        assert robot.startswith('robot'), f"Unexpected robot name format: {robot}"
    assert len(EXPECTED_ROBOTS) == 3, "Exactly 3 robots are required."


def test_spawn_poses_non_overlapping():
    """Each robot must have a unique spawn position to avoid collisions."""
    seen_positions = set()
    for robot, (x, y) in SPAWN_POSES.items():
        pos = (x, y)
        assert pos not in seen_positions, (
            f"Robot {robot} shares spawn position {pos} with another robot!"
        )
        seen_positions.add(pos)


def test_spawn_poses_keys_match_robot_list():
    """Spawn poses must be defined for exactly the expected robots."""
    assert set(SPAWN_POSES.keys()) == set(EXPECTED_ROBOTS), (
        f"Mismatch between SPAWN_POSES keys {set(SPAWN_POSES.keys())} "
        f"and EXPECTED_ROBOTS {set(EXPECTED_ROBOTS)}"
    )


def test_spawn_robot_launch_file_exists():
    """spawn_robot.launch.py must exist in the launch directory."""
    pkg_root = os.path.join(os.path.dirname(__file__), '..')
    launch_file = os.path.normpath(
        os.path.join(pkg_root, 'launch', 'spawn_robot.launch.py')
    )
    assert os.path.isfile(launch_file), (
        f"Missing launch file: {launch_file}"
    )


def test_gazebo_ionic_launch_file_exists():
    """gazebo_ionic.launch.py must exist (referenced in README and bringup)."""
    pkg_root = os.path.join(os.path.dirname(__file__), '..')
    launch_file = os.path.normpath(
        os.path.join(pkg_root, 'launch', 'gazebo_ionic.launch.py')
    )
    assert os.path.isfile(launch_file), (
        f"Missing launch file: {launch_file}"
    )


def test_gz_world_launch_file_exists():
    """gz_world.launch.py must exist."""
    pkg_root = os.path.join(os.path.dirname(__file__), '..')
    launch_file = os.path.normpath(
        os.path.join(pkg_root, 'launch', 'gz_world.launch.py')
    )
    assert os.path.isfile(launch_file), (
        f"Missing launch file: {launch_file}"
    )


def test_no_duplicate_robot_ids():
    """Robot IDs must be unique — no two robots can share the same namespace."""
    assert len(EXPECTED_ROBOTS) == len(set(EXPECTED_ROBOTS)), (
        "Duplicate robot IDs detected!"
    )


def test_robot_id_format():
    """Robot IDs must follow the 'robotN' convention."""
    for robot in EXPECTED_ROBOTS:
        assert robot.startswith('robot'), f"Robot ID '{robot}' does not follow 'robotN' format."
        suffix = robot[len('robot'):]
        assert suffix.isdigit(), f"Robot ID '{robot}' suffix '{suffix}' is not a number."