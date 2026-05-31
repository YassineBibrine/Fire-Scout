from __future__ import annotations

import math
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Iterable, Optional

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
from sensor_msgs.msg import LaserScan

FusionDecision = getattr(import_module('firescout_interfaces.msg'), 'FusionDecision')


@dataclass(frozen=True)
class SectorClearance:
    front: float
    left: float
    right: float


@dataclass(frozen=True)
class FusionDecisionSnapshot:
    risk_level: float
    recommended_action: str


def _finite_min(values: Iterable[float], default: float) -> float:
    finite_values = [float(value) for value in values if math.isfinite(float(value))]
    return min(finite_values) if finite_values else default


def scan_clearance(scan: LaserScan, front_angle_rad: float) -> SectorClearance:
    """Return minimum scan ranges in front, front-left, and front-right sectors."""
    ranges = list(scan.ranges)
    if not ranges:
        return SectorClearance(front=math.inf, left=math.inf, right=math.inf)

    angle_min = float(scan.angle_min)
    angle_increment = float(scan.angle_increment)
    range_max = float(scan.range_max) if math.isfinite(float(scan.range_max)) else math.inf
    if angle_increment == 0.0:
        return SectorClearance(front=math.inf, left=math.inf, right=math.inf)

    front_values = []
    left_values = []
    right_values = []
    for index, distance in enumerate(ranges):
        angle = math.atan2(
            math.sin(angle_min + index * angle_increment),
            math.cos(angle_min + index * angle_increment),
        )
        if abs(angle) <= front_angle_rad:
            front_values.append(distance)
        elif 0.0 < angle <= 2.0 * front_angle_rad:
            left_values.append(distance)
        elif -2.0 * front_angle_rad <= angle < 0.0:
            right_values.append(distance)

    return SectorClearance(
        front=_finite_min(front_values, range_max),
        left=_finite_min(left_values, range_max),
        right=_finite_min(right_values, range_max),
    )


def limit_twist_for_obstacles(
    command: Twist,
    clearance: Optional[SectorClearance],
    stop_distance_m: float,
    slow_distance_m: float,
    avoidance_turn_speed: float,
    escape_reverse_speed: float,
) -> Twist:
    """Clamp a velocity command using simple lidar obstacle clearances."""
    safe = Twist()
    safe.linear.x = command.linear.x
    safe.linear.y = command.linear.y
    safe.linear.z = command.linear.z
    safe.angular.x = command.angular.x
    safe.angular.y = command.angular.y
    safe.angular.z = command.angular.z

    if clearance is None or safe.linear.x <= 0.0:
        return safe

    if clearance.front <= stop_distance_m:
        safe.linear.x = -abs(escape_reverse_speed)
        turn_direction = 1.0 if clearance.left >= clearance.right else -1.0
        safe.angular.z = turn_direction * max(abs(safe.angular.z), avoidance_turn_speed)
        return safe

    if clearance.front < slow_distance_m:
        span = max(slow_distance_m - stop_distance_m, 1e-6)
        scale = max(0.0, min(1.0, (clearance.front - stop_distance_m) / span))
        safe.linear.x *= scale

    return safe


def should_bypass_risk_speed_limit(decision: Optional[FusionDecisionSnapshot]) -> bool:
    if decision is None:
        return False
    return decision.recommended_action in {'SUPPRESS', 'RESCUE'}


# Backward-compatible helper name retained for existing callers/tests.
should_bypass_obstacle_safety = should_bypass_risk_speed_limit


def apply_risk_speed_limit(
    command: Twist,
    decision: Optional[FusionDecisionSnapshot],
    risk_threshold: float,
    max_linear_speed: float,
) -> Twist:
    safe = Twist()
    safe.linear.x = command.linear.x
    safe.linear.y = command.linear.y
    safe.linear.z = command.linear.z
    safe.angular.x = command.angular.x
    safe.angular.y = command.angular.y
    safe.angular.z = command.angular.z

    if decision is None:
        return safe

    if decision.risk_level <= risk_threshold:
        return safe

    limit = max(float(max_linear_speed), 0.0)
    if limit == 0.0:
        safe.linear.x = 0.0
        return safe

    safe.linear.x = max(-limit, min(limit, safe.linear.x))
    return safe


class CmdVelSafetyNode(Node):
    """Filter commanded velocity with a local lidar-based obstacle reflex."""

    def __init__(self) -> None:
        super().__init__('cmd_vel_safety_node')

        self.declare_parameter('robot_id', 'robot1')
        self.declare_parameter('front_angle_deg', 45.0)
        self.declare_parameter('stop_distance_m', 0.55)
        self.declare_parameter('slow_distance_m', 1.1)
        self.declare_parameter('avoidance_turn_speed', 1.15)
        self.declare_parameter('escape_reverse_speed', 0.12)
        self.declare_parameter('risk_level_threshold', 0.8)
        self.declare_parameter('high_risk_max_linear_speed', 0.1)

        self._robot_id = str(self.get_parameter('robot_id').value)
        self._front_angle_rad = math.radians(float(self.get_parameter('front_angle_deg').value))
        self._stop_distance_m = max(float(self.get_parameter('stop_distance_m').value), 0.0)
        self._slow_distance_m = max(float(self.get_parameter('slow_distance_m').value), self._stop_distance_m)
        self._avoidance_turn_speed = max(float(self.get_parameter('avoidance_turn_speed').value), 0.0)
        self._escape_reverse_speed = max(float(self.get_parameter('escape_reverse_speed').value), 0.0)
        self._risk_level_threshold = float(self.get_parameter('risk_level_threshold').value)
        self._high_risk_max_linear_speed = max(
            float(self.get_parameter('high_risk_max_linear_speed').value),
            0.0,
        )

        self._latest_clearance: Optional[SectorClearance] = None
        self._latest_decision: Optional[FusionDecisionSnapshot] = None
        fusion_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=5,
            reliability=ReliabilityPolicy.RELIABLE,
        )
        self._safe_pub = self.create_publisher(Twist, f'/{self._robot_id}/cmd_vel_safe', 10)
        self.create_subscription(Twist, f'/{self._robot_id}/cmd_vel', self._cmd_callback, 10)
        self.create_subscription(
            LaserScan,
            f'/{self._robot_id}/scan',
            self._scan_callback,
            qos_profile_sensor_data,
        )
        self.create_subscription(
            FusionDecision,
            f'/{self._robot_id}/fusion_decision',
            self._fusion_callback,
            fusion_qos,
        )

        self.get_logger().info(
            f'CmdVelSafetyNode started for {self._robot_id}: '
            f'/{self._robot_id}/cmd_vel -> /{self._robot_id}/cmd_vel_safe'
        )

    def _scan_callback(self, msg: LaserScan) -> None:
        self._latest_clearance = scan_clearance(msg, self._front_angle_rad)

    def _fusion_callback(self, msg: Any) -> None:
        self._latest_decision = FusionDecisionSnapshot(
            risk_level=float(msg.risk_level),
            recommended_action=str(msg.recommended_action),
        )

    def _cmd_callback(self, msg: Twist) -> None:
        decision = self._latest_decision

        # For critical actions (SUPPRESS/RESCUE), publish full passthrough —
        # keep obstacle avoidance active but allow the task speed policy through.
        safe = limit_twist_for_obstacles(
            msg,
            self._latest_clearance,
            self._stop_distance_m,
            self._slow_distance_m,
            self._avoidance_turn_speed,
            self._escape_reverse_speed,
        )
        if not should_bypass_risk_speed_limit(decision):
            safe = apply_risk_speed_limit(
                safe,
                decision,
                self._risk_level_threshold,
                self._high_risk_max_linear_speed,
            )
        self._safe_pub.publish(safe)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = CmdVelSafetyNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
