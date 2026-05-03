"""
test_clock_available.py
=======================
Validates that:
  - sim_physics.yaml is present and configures real_time_factor
  - All launch files use use_sim_time=true by default
  - The clock topic will be available (use_sim_time is set consistently)

These tests do NOT require a running Gazebo instance.
"""

import os
import pytest

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# ── Paths ────────────────────────────────────────────────────────────────────

PKG_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

SIM_PHYSICS_YAML = os.path.join(PKG_ROOT, 'config', 'sim_physics.yaml')
SPAWN_LAUNCH     = os.path.join(PKG_ROOT, 'launch', 'spawn_robot.launch.py')
BRIDGE_LAUNCH    = os.path.join(PKG_ROOT, 'launch', 'bridge_robot.launch.py')
GAZEBO_LAUNCH    = os.path.join(PKG_ROOT, 'launch', 'gazebo_ionic.launch.py')
GZ_WORLD_LAUNCH  = os.path.join(PKG_ROOT, 'launch', 'gz_world.launch.py')


# ── Helpers ──────────────────────────────────────────────────────────────────

def _read(path: str) -> str:
    with open(path, 'r') as f:
        return f.read()


# ── Tests ────────────────────────────────────────────────────────────────────

def test_sim_physics_yaml_exists():
    """sim_physics.yaml must exist in config/."""
    assert os.path.isfile(SIM_PHYSICS_YAML), f"Missing: {SIM_PHYSICS_YAML}"


@pytest.mark.skipif(not HAS_YAML, reason="pyyaml not installed")
def test_sim_physics_real_time_factor():
    """sim_physics.yaml must declare real_time_factor."""
    with open(SIM_PHYSICS_YAML, 'r') as f:
        cfg = yaml.safe_load(f)
    rtf = (
        cfg.get('simulation', {})
           .get('ros__parameters', {})
           .get('real_time_factor')
    )
    assert rtf is not None, "real_time_factor not defined in sim_physics.yaml."
    assert isinstance(rtf, (int, float)), "real_time_factor must be a number."
    assert rtf > 0, f"real_time_factor must be > 0, got {rtf}."


def test_spawn_launch_declares_use_sim_time():
    """spawn_robot.launch.py must declare use_sim_time argument."""
    content = _read(SPAWN_LAUNCH)
    assert 'use_sim_time' in content, (
        "spawn_robot.launch.py does not declare 'use_sim_time'."
    )


def test_spawn_launch_sim_time_default_true():
    """spawn_robot.launch.py must default use_sim_time to 'true'."""
    content = _read(SPAWN_LAUNCH)
    # The argument declaration should have default_value='true'
    assert "'true'" in content or '"true"' in content, (
        "spawn_robot.launch.py does not set use_sim_time default to 'true'."
    )


def test_bridge_launch_declares_use_sim_time():
    """bridge_robot.launch.py must declare use_sim_time argument."""
    content = _read(BRIDGE_LAUNCH)
    assert 'use_sim_time' in content, (
        "bridge_robot.launch.py does not declare 'use_sim_time'."
    )


def test_gazebo_ionic_declares_use_sim_time():
    """gazebo_ionic.launch.py must declare use_sim_time argument."""
    content = _read(GAZEBO_LAUNCH)
    assert 'use_sim_time' in content, (
        "gazebo_ionic.launch.py does not declare 'use_sim_time'."
    )


def test_gz_world_launch_references_gz_sim():
    """gz_world.launch.py must reference 'gz_sim' to start Gazebo."""
    content = _read(GZ_WORLD_LAUNCH)
    assert 'gz_sim' in content, (
        "gz_world.launch.py does not reference 'gz_sim'."
    )


def test_gazebo_ionic_propagates_use_sim_time_to_robots():
    """gazebo_ionic.launch.py must pass use_sim_time to spawn and bridge sub-launches."""
    content = _read(GAZEBO_LAUNCH)
    assert content.count('use_sim_time') >= 3, (
        "gazebo_ionic.launch.py should propagate use_sim_time to each sub-launch."
    )


def test_config_directory_contains_sim_physics():
    """The config/ directory must contain sim_physics.yaml."""
    config_dir = os.path.join(PKG_ROOT, 'config')
    assert os.path.isdir(config_dir), f"config/ directory missing: {config_dir}"
    files = os.listdir(config_dir)
    assert 'sim_physics.yaml' in files, (
        f"sim_physics.yaml not found in config/. Found: {files}"
    )