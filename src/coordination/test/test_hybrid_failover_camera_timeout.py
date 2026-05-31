import pytest

pytest.importorskip('rclpy')

from rclpy.time import Time

from coordination.health_monitor_node import evaluate_robot_timeout_errors


def test_camera_timeout_emits_error_token():
    now = Time(seconds=10.0)
    last_heartbeat = Time(seconds=9.5)
    last_fusion = Time(seconds=1.0)

    errors = evaluate_robot_timeout_errors(
        'robot1',
        now,
        last_heartbeat,
        last_fusion,
        heartbeat_timeout_sec=5.0,
        fusion_timeout_sec=5.0,
    )

    assert 'camera_sensor_timeout:robot1' in errors
