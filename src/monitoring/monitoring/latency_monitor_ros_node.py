"""ROS node wrapper for latency monitoring."""

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from monitoring.latency_monitor_node import LatencyMonitor


class LatencyMonitorRosNode(Node):
    def __init__(self):
        super().__init__('latency_monitor_node')
        threshold_s = float(self.declare_parameter('latency_threshold_s', 0.2).value)
        self.monitor = LatencyMonitor(threshold_s=threshold_s)
        self.create_subscription(String, 'monitoring/latency_samples', self._on_sample, 10)
        self.pub = self.create_publisher(String, 'monitoring/latency_alarm', 10)

    def _on_sample(self, msg):
        try:
            payload = json.loads(msg.data)
            sent_ts_s = float(payload['sent_ts_s'])
            recv_ts_s = float(payload['recv_ts_s'])
        except (KeyError, ValueError, TypeError, json.JSONDecodeError):
            self.get_logger().warning('Invalid latency sample payload')
            return

        alarm_state = self.monitor.observe(sent_ts_s, recv_ts_s)
        out = String()
        out.data = json.dumps({'alarm': alarm_state, 'latency_s': self.monitor.last_latency_s})
        self.pub.publish(out)


def main():
    rclpy.init()
    node = LatencyMonitorRosNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
