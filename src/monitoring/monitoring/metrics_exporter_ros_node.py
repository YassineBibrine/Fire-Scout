"""ROS node wrapper exporting metrics snapshots."""

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from monitoring.metrics_exporter_node import export_metrics


class MetricsExporterRosNode(Node):
    def __init__(self):
        super().__init__('metrics_exporter_node')
        self.metrics = {'latency_alarm_count': 0, 'rate_alarm_count': 0}
        self.create_subscription(String, 'monitoring/latency_alarm', self._on_latency, 10)
        self.create_subscription(String, 'monitoring/topic_rate_alarm', self._on_rate, 10)
        self.pub = self.create_publisher(String, 'monitoring/metrics', 10)
        self.create_timer(1.0, self._publish_metrics)

    def _on_latency(self, msg):
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        if payload.get('alarm'):
            self.metrics['latency_alarm_count'] += 1

    def _on_rate(self, msg):
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        if payload.get('alarm'):
            self.metrics['rate_alarm_count'] += 1

    def _publish_metrics(self):
        out = String()
        out.data = export_metrics(self.metrics)
        self.pub.publish(out)


def main():
    rclpy.init()
    node = MetricsExporterRosNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
