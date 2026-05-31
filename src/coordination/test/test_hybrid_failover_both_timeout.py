import importlib.util
from pathlib import Path

import pytest

pytest.importorskip('rclpy')


def _load_mission_manager_module():
    module_path = Path(__file__).resolve().parents[1] / 'coordination' / 'mission_manager_node.py'
    spec = importlib.util.spec_from_file_location('mission_manager_node', str(module_path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_mission_manager = _load_mission_manager_module()
should_enter_safe_stop = _mission_manager.should_enter_safe_stop


def test_safe_stop_when_all_camera_timeouts_present():
    robots = ['robot1', 'robot2', 'robot3']
    error_message = (
        'camera_sensor_timeout:robot1,'
        'camera_sensor_timeout:robot2,'
        'camera_sensor_timeout:robot3,'
        'heartbeat_timeout:robot1'
    )

    assert should_enter_safe_stop(robots, error_message)


def test_safe_stop_not_triggered_for_partial_timeouts():
    robots = ['robot1', 'robot2', 'robot3']
    error_message = 'camera_sensor_timeout:robot1,camera_sensor_timeout:robot3'

    assert not should_enter_safe_stop(robots, error_message)
