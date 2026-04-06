"""ROS node wrapper for topic-rate monitoring."""

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from monitoring.topic_rate_monitor_node import TopicRateMonitor


class TopicRateMonitorRosNode(Node):
    def __init__(self):
        super().__init__('topic_rate_monitor_node')
        minimum_rate_hz = float(self.declare_parameter('minimum_rate_hz', 2.0).value)
        window_s = float(self.declare_parameter('window_s', 2.0).value)
        self.monitor = TopicRateMonitor(minimum_rate_hz=minimum_rate_hz, window_s=window_s)
        self.create_subscription(String, 'monitoring/rate_samples', self._on_sample, 10)
        self.pub = self.create_publisher(String, 'monitoring/topic_rate_alarm', 10)

    def _on_sample(self, msg):
        try:
            payload = json.loads(msg.data)
            timestamp_s = float(payload['timestamp_s'])
        except (KeyError, ValueError, TypeError, json.JSONDecodeError):
            self.get_logger().warning('Invalid rate sample payload')
            return

        self.monitor.record(timestamp_s)
        out = String()
        out.data = json.dumps({'alarm': self.monitor.alarm(), 'rate_hz': self.monitor.current_rate()})
        self.pub.publish(out)


def main():
    rclpy.init()
    node = TopicRateMonitorRosNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
