import pytest

pytest.importorskip('geometry_msgs.msg')
pytest.importorskip('sensor_msgs.msg')

from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan

from coordination.cmd_vel_safety_node import (
    SectorClearance,
    limit_twist_for_obstacles,
    scan_clearance,
)


def _forward_command(speed: float = 0.3) -> Twist:
    command = Twist()
    command.linear.x = speed
    return command


def test_obstacle_ahead_reverses_and_turns_to_clearer_left_side():
    safe = limit_twist_for_obstacles(
        _forward_command(),
        SectorClearance(front=0.2, left=1.2, right=0.4),
        stop_distance_m=0.45,
        slow_distance_m=0.9,
        avoidance_turn_speed=0.8,
        escape_reverse_speed=0.12,
    )

    assert safe.linear.x == pytest.approx(-0.12)
    assert safe.angular.z == pytest.approx(0.8)


def test_obstacle_ahead_reverses_and_turns_to_clearer_right_side():
    safe = limit_twist_for_obstacles(
        _forward_command(),
        SectorClearance(front=0.2, left=0.3, right=1.1),
        stop_distance_m=0.45,
        slow_distance_m=0.9,
        avoidance_turn_speed=0.8,
        escape_reverse_speed=0.12,
    )

    assert safe.linear.x == pytest.approx(-0.12)
    assert safe.angular.z == pytest.approx(-0.8)


def test_near_obstacle_slows_forward_motion():
    safe = limit_twist_for_obstacles(
        _forward_command(speed=0.4),
        SectorClearance(front=0.675, left=1.0, right=1.0),
        stop_distance_m=0.45,
        slow_distance_m=0.9,
        avoidance_turn_speed=0.8,
        escape_reverse_speed=0.12,
    )

    assert 0.0 < safe.linear.x < 0.4
    assert safe.angular.z == 0.0


def test_reverse_motion_is_not_clamped_by_front_obstacle():
    command = _forward_command(speed=-0.2)
    safe = limit_twist_for_obstacles(
        command,
        SectorClearance(front=0.2, left=1.2, right=0.4),
        stop_distance_m=0.45,
        slow_distance_m=0.9,
        avoidance_turn_speed=0.8,
        escape_reverse_speed=0.12,
    )

    assert safe.linear.x == pytest.approx(-0.2)
    assert safe.angular.z == 0.0


def test_scan_clearance_reads_front_sector_around_zero_angle():
    scan = LaserScan()
    scan.angle_min = -1.0
    scan.angle_increment = 0.5
    scan.range_max = 5.0
    scan.ranges = [2.0, 1.0, 0.25, 1.5, 2.5]

    clearance = scan_clearance(scan, front_angle_rad=0.3)

    assert clearance.front == pytest.approx(0.25)
    assert clearance.left == pytest.approx(1.5)
    assert clearance.right == pytest.approx(1.0)
