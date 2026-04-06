"""ROS 2 health monitor node for heartbeat timeout detection."""

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from coordination.heartbeat_monitor import heartbeat_timed_out


class HealthNode(Node):
    def __init__(self):
        super().__init__('health_node')
        self.timeout_s = float(self.declare_parameter('timeout_s', 2.0).value)
        self.check_period_s = float(self.declare_parameter('check_period_s', 0.5).value)
        self.last_seen = {}

        self.create_subscription(String, 'heartbeat', self._on_heartbeat, 10)
        self.alarm_pub = self.create_publisher(String, 'coordination/health_alarm', 10)
        self.create_timer(self.check_period_s, self._check_timeouts)

    def _on_heartbeat(self, msg):
        try:
            payload = json.loads(msg.data)
            robot_id = payload['robot_id']
            ts = float(payload['timestamp_s'])
        except (KeyError, ValueError, TypeError, json.JSONDecodeError):
            self.get_logger().warning('Invalid heartbeat payload')
            return

        self.last_seen[robot_id] = ts

    def _check_timeouts(self):
        now_s = self.get_clock().now().nanoseconds / 1e9
        for robot_id, last_seen_s in self.last_seen.items():
            if heartbeat_timed_out(last_seen_s, now_s, self.timeout_s):
                alarm = String()
                alarm.data = json.dumps({'robot_id': robot_id, 'status': 'timeout'})
                self.alarm_pub.publish(alarm)


def main():
    rclpy.init()
    node = HealthNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
