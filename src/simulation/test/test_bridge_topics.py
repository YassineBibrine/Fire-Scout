"""
test_bridge_topics.py
=====================
Validates that bridge_robot.launch.py is consistent with bridge_topics_robot.yaml
and that all required topics are declared for bridging.

These tests do NOT require a running Gazebo instance.
"""

import os
import pytest


# ── Constants ────────────────────────────────────────────────────────────────

REQUIRED_TOPICS = ['scan', 'odom', 'imu', 'camera', 'cmd_vel', 'tf']

EXPECTED_ROBOTS = ['robot1', 'robot2', 'robot3']

BRIDGE_LAUNCH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', 'launch', 'bridge_robot.launch.py')
)

CONFIG_YAML = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', 'config', 'bridge_topics_robot.yaml')
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _read_file(path: str) -> str:
    with open(path, 'r') as f:
        return f.read()


# ── Tests ────────────────────────────────────────────────────────────────────

def test_bridge_launch_file_exists():
    """bridge_robot.launch.py must exist."""
    assert os.path.isfile(BRIDGE_LAUNCH), f"Missing: {BRIDGE_LAUNCH}"


def test_bridge_config_yaml_exists():
    """bridge_topics_robot.yaml must exist."""
    assert os.path.isfile(CONFIG_YAML), f"Missing: {CONFIG_YAML}"


def test_bridge_launch_contains_scan():
    """bridge_robot.launch.py must bridge the /scan topic (LiDAR)."""
    content = _read_file(BRIDGE_LAUNCH)
    assert 'scan' in content, (
        "bridge_robot.launch.py does not bridge 'scan' (LiDAR topic missing)."
    )


def test_bridge_launch_contains_imu():
    """bridge_robot.launch.py must bridge the /imu topic."""
    content = _read_file(BRIDGE_LAUNCH)
    assert 'imu' in content, (
        "bridge_robot.launch.py does not bridge 'imu' (IMU topic missing)."
    )


def test_bridge_launch_contains_camera():
    """bridge_robot.launch.py must bridge the /camera topic."""
    content = _read_file(BRIDGE_LAUNCH)
    assert 'camera' in content, (
        "bridge_robot.launch.py does not bridge 'camera' (Camera topic missing)."
    )


def test_bridge_launch_contains_cmd_vel():
    """bridge_robot.launch.py must bridge cmd_vel (ROS → Gz)."""
    content = _read_file(BRIDGE_LAUNCH)
    assert 'cmd_vel' in content, (
        "bridge_robot.launch.py does not bridge 'cmd_vel'."
    )


def test_bridge_launch_contains_odom():
    """bridge_robot.launch.py must bridge odometry (Gz → ROS)."""
    content = _read_file(BRIDGE_LAUNCH)
    assert 'odom' in content or 'odometry' in content, (
        "bridge_robot.launch.py does not bridge 'odom'/'odometry'."
    )


def test_bridge_launch_contains_tf():
    """bridge_robot.launch.py must bridge /tf."""
    content = _read_file(BRIDGE_LAUNCH)
    assert 'tf' in content, (
        "bridge_robot.launch.py does not bridge 'tf'."
    )


def test_config_yaml_lists_required_topics():
    """bridge_topics_robot.yaml must list scan, odom, imu, camera."""
    content = _read_file(CONFIG_YAML)
    for topic in ['scan', 'odom', 'imu', 'camera']:
        assert topic in content, (
            f"bridge_topics_robot.yaml is missing topic '{topic}'."
        )


def test_bridge_launch_uses_ros_gz_bridge():
    """bridge_robot.launch.py must use the ros_gz_bridge package."""
    content = _read_file(BRIDGE_LAUNCH)
    assert 'ros_gz_bridge' in content, (
        "bridge_robot.launch.py does not reference 'ros_gz_bridge'."
    )


def test_bridge_launch_uses_parameter_bridge():
    """bridge_robot.launch.py must use 'parameter_bridge' executable."""
    content = _read_file(BRIDGE_LAUNCH)
    assert 'parameter_bridge' in content, (
        "bridge_robot.launch.py does not use 'parameter_bridge' executable."
    )


def test_bridge_covers_all_yaml_topics():
    """Every topic in bridge_topics_robot.yaml must appear in bridge_robot.launch.py."""
    import yaml
    with open(CONFIG_YAML, 'r') as f:
        cfg = yaml.safe_load(f)

    topics = (
        cfg.get('simulation', {})
           .get('ros__parameters', {})
           .get('bridged_topics', [])
    )
    assert topics, "bridge_topics_robot.yaml has no 'bridged_topics' list."

    bridge_content = _read_file(BRIDGE_LAUNCH)
    for topic in topics:
        assert topic in bridge_content, (
            f"Topic '{topic}' is in bridge_topics_robot.yaml "
            f"but not in bridge_robot.launch.py."
        )