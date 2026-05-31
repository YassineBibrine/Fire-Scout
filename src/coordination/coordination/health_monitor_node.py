from importlib import import_module
from typing import Any, Dict, List, Optional

import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from rclpy.time import Time
from std_msgs.msg import String

# Resolve the generated ROS message classes dynamically to avoid static analyzer
# false positives when interface stubs are not discoverable in the IDE env.
NodeStatusMsg = Any
RobotHealthMsg = Any

RobotHealth = getattr(import_module('firescout_interfaces.msg'), 'RobotHealth')
NodeStatus = getattr(import_module('firescout_interfaces.msg'), 'NodeStatus')
FusionDecision = getattr(import_module('firescout_interfaces.msg'), 'FusionDecision')


def _elapsed_seconds(now: Time, last_seen: Optional[Time]) -> Optional[float]:
    if last_seen is None:
        return None
    return (now - last_seen).nanoseconds / 1e9


def evaluate_robot_timeout_errors(
    robot_id: str,
    now: Time,
    last_heartbeat: Optional[Time],
    last_fusion: Optional[Time],
    heartbeat_timeout_sec: float,
    fusion_timeout_sec: float,
    startup_elapsed_sec: float = float('inf'),
    startup_grace_sec: float = 0.0,
) -> List[str]:
    errors = []
    heartbeat_elapsed = _elapsed_seconds(now, last_heartbeat)
    if heartbeat_elapsed is None or heartbeat_elapsed > heartbeat_timeout_sec:
        errors.append(f'heartbeat_timeout:{robot_id}')

    fusion_elapsed = _elapsed_seconds(now, last_fusion)
    if (
        startup_elapsed_sec > startup_grace_sec
        and (fusion_elapsed is None or fusion_elapsed > fusion_timeout_sec)
    ):
        errors.append(f'camera_sensor_timeout:{robot_id}')

    return errors


class HealthMonitorNode(Node):

    def __init__(self):

        super().__init__('health_monitor_node')

        self.declare_parameter(
            'heartbeat_timeout_sec',
            2.0
        )
        self.declare_parameter('fusion_timeout_sec', 5.0)
        self.declare_parameter('startup_grace_sec', 20.0)

        if not self.has_parameter('use_sim_time'):
            self.declare_parameter(
                'use_sim_time',
                True
            )

        self.heartbeat_timeout_sec = self.get_parameter(
            'heartbeat_timeout_sec'
        ).value
        self.fusion_timeout_sec = float(self.get_parameter('fusion_timeout_sec').value)
        self.startup_grace_sec = float(self.get_parameter('startup_grace_sec').value)

        self.declare_parameter('robot_ids', ['robot1', 'robot2', 'robot3'])
        robot_ids = list(self.get_parameter('robot_ids').value)
        self.robots = [str(robot) for robot in robot_ids if str(robot)] or ['robot1', 'robot2', 'robot3']
        self.last_heartbeat: Dict[str, Optional[Time]] = {robot: None for robot in self.robots}
        self.last_fusion: Dict[str, Optional[Time]] = {robot: None for robot in self.robots}
        self.degraded_robots = set()
        self.start_time = self.get_clock().now()
        fusion_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=5,
            reliability=ReliabilityPolicy.RELIABLE,
        )

        for robot in self.robots:
            self.create_subscription(
                RobotHealth,
                f'/{robot}/robot_health',
                self._make_robot_health_callback(robot),
                10
            )

            self.create_subscription(
                String,
                f'/mapping/{robot}/slam_status',
                self._make_slam_status_callback(robot),
                10
            )

            self.create_subscription(
                FusionDecision,
                f'/{robot}/fusion_decision',
                self._make_fusion_callback(robot),
                fusion_qos
            )

        self.publisher_ = self.create_publisher(
            NodeStatus,
            '/coordination/system_health',
            10
        )

        self.timer = self.create_timer(
            1.0,
            self.publish_health_status
        )

        self.get_logger().info(
            'Health Monitor Node started'
        )

    def _make_robot_health_callback(self, robot_id: str):

        def _callback(msg: RobotHealthMsg) -> None:
            self.robot_health_callback(msg, robot_id)

        return _callback

    def _make_slam_status_callback(self, robot_id: str):

        def _callback(msg: String) -> None:
            self._on_slam_status(msg, robot_id)

        return _callback

    def _make_fusion_callback(self, robot_id: str):

        def _callback(_msg: Any) -> None:
            self.last_fusion[robot_id] = self.get_clock().now()

        return _callback

    def robot_health_callback(self, _msg: RobotHealthMsg, robot_id: str) -> None:
        self.last_heartbeat[robot_id] = self.get_clock().now()

    def _on_slam_status(self, msg: String, robot_id: str) -> None:
        self.last_heartbeat[robot_id] = self.get_clock().now()

    def publish_health_status(self):

        now = self.get_clock().now()
        degraded = []
        error_tokens: List[str] = []

        for robot in self.robots:
            errors = evaluate_robot_timeout_errors(
                robot,
                now,
                self.last_heartbeat.get(robot),
                self.last_fusion.get(robot),
                float(self.heartbeat_timeout_sec),
                float(self.fusion_timeout_sec),
                startup_elapsed_sec=(now - self.start_time).nanoseconds / 1e9,
                startup_grace_sec=float(self.startup_grace_sec),
            )
            if errors:
                degraded.append(robot)
                error_tokens.extend(errors)
                if robot not in self.degraded_robots:
                    self.degraded_robots.add(robot)
                    self.get_logger().warning(
                        f"Robot {robot} is DEGRADED ({', '.join(errors)})"
                    )
            else:
                if robot in self.degraded_robots:
                    self.degraded_robots.remove(robot)

        status = NodeStatus()
        status.node_name = 'system_health'
        status.status = 'HEALTHY' if not degraded else 'DEGRADED'
        status.error_message = ','.join(error_tokens)
        status.uptime_seconds = (
            (now - self.start_time).nanoseconds / 1e9
        )
        status.last_heartbeat = now.to_msg()

        self.publisher_.publish(status)


def main(args=None):

    rclpy.init(args=args)

    node = HealthMonitorNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
