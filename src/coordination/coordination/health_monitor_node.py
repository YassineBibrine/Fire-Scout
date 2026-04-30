from importlib import import_module
from typing import Any, Dict, Optional

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from std_msgs.msg import String

# Resolve the generated ROS message classes dynamically to avoid static analyzer
# false positives when interface stubs are not discoverable in the IDE env.
NodeStatusMsg = Any
RobotHealthMsg = Any

RobotHealth = getattr(import_module('firescout_interfaces.msg'), 'RobotHealth')
NodeStatus = getattr(import_module('firescout_interfaces.msg'), 'NodeStatus')


class HealthMonitorNode(Node):

    def __init__(self):

        super().__init__('health_monitor_node')

        self.declare_parameter(
            'heartbeat_timeout_sec',
            2.0
        )

        if not self.has_parameter('use_sim_time'):
            self.declare_parameter(
                'use_sim_time',
                True
            )

        self.heartbeat_timeout_sec = self.get_parameter(
            'heartbeat_timeout_sec'
        ).value

        self.robots = ['robot1', 'robot2', 'robot3']
        self.last_seen: Dict[str, Optional[Time]] = {robot: None for robot in self.robots}
        self.degraded_robots = set()
        self.start_time = self.get_clock().now()

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

    def robot_health_callback(self, _msg: RobotHealthMsg, robot_id: str) -> None:

        self.last_seen[robot_id] = self.get_clock().now()

    def _on_slam_status(self, msg: String, robot_id: str) -> None:

        self.last_seen[robot_id] = self.get_clock().now()

    def publish_health_status(self):

        now = self.get_clock().now()
        degraded = []

        for robot in self.robots:
            last_seen = self.last_seen.get(robot)

            if last_seen is None:
                is_degraded = True
            else:
                elapsed = (now - last_seen).nanoseconds / 1e9
                is_degraded = elapsed > self.heartbeat_timeout_sec

            if is_degraded:
                degraded.append(robot)
                if robot not in self.degraded_robots:
                    self.degraded_robots.add(robot)
                    self.get_logger().warning(
                        f"Robot {robot} is DEGRADED"
                    )
            else:
                if robot in self.degraded_robots:
                    self.degraded_robots.remove(robot)

        status = NodeStatus()
        status.node_name = 'system_health'
        status.status = 'HEALTHY' if not degraded else 'DEGRADED'
        status.error_message = ','.join(degraded)
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
