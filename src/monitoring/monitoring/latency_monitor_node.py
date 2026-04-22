#!/usr/bin/env python3

"""Monitor message transport latency for header-bearing topics."""

from typing import Callable, Dict, List

import rclpy
from nav_msgs.msg import OccupancyGrid, Odometry
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String


class LatencyMonitorNode(Node):
    """Computes now - msg.header.stamp and emits ALARM/OK status messages."""

    def __init__(self) -> None:
        super().__init__('latency_monitor_node')

        # Generic and per-type latency thresholds (ms).
        self.declare_parameter('default_max_latency_ms', 500.0)
        self.declare_parameter('scan_max_latency_ms', 200.0)
        self.declare_parameter('odom_max_latency_ms', 100.0)
        self.declare_parameter('map_max_latency_ms', 2000.0)

        # Preferred config interface from monitor_topics.yaml.
        self.declare_parameter('monitored_topics', [''])

        # Backward-compatible fallback list.
        self.declare_parameter('topics', [''])

        self._default_max_latency_ms = float(self.get_parameter('default_max_latency_ms').value)
        self._scan_max_latency_ms = float(self.get_parameter('scan_max_latency_ms').value)
        self._odom_max_latency_ms = float(self.get_parameter('odom_max_latency_ms').value)
        self._map_max_latency_ms = float(self.get_parameter('map_max_latency_ms').value)

        monitored_topics = [t for t in list(self.get_parameter('monitored_topics').value) if t]
        if not monitored_topics:
            monitored_topics = [t for t in list(self.get_parameter('topics').value) if t]

        self._alarm_pub = self.create_publisher(String, '/monitoring/latency_alarm', 10)
        self._subscriptions = []

        # Subscribe only to known message types that carry std_msgs/Header.
        for topic in monitored_topics:
            msg_type = self._infer_msg_type(topic)
            if msg_type is None:
                continue

            callback = self._make_latency_callback(topic)
            self._subscriptions.append(self.create_subscription(msg_type, topic, callback, 10))

        self.get_logger().info(
            f'LatencyMonitorNode started with {len(self._subscriptions)} header topics.'
        )

    def _infer_msg_type(self, topic: str):
        """Infer ROS message type from Fire-Scout topic naming conventions."""
        if topic.endswith('/scan'):
            return LaserScan
        if topic.endswith('/odom'):
            return Odometry
        if topic.endswith('/map') or topic == '/map':
            return OccupancyGrid
        return None

    def _threshold_for_topic(self, topic: str) -> float:
        """Resolve topic-specific latency threshold in milliseconds."""
        if topic.endswith('/scan'):
            return self._scan_max_latency_ms
        if topic.endswith('/odom'):
            return self._odom_max_latency_ms
        if topic.endswith('/map') or topic == '/map':
            return self._map_max_latency_ms
        return self._default_max_latency_ms

    def _make_latency_callback(self, topic: str) -> Callable:
        """Create callback computing latency and publishing ALARM/OK."""

        def _callback(msg) -> None:
            now_ns = self.get_clock().now().nanoseconds
            stamp_ns = int(msg.header.stamp.sec) * 1000000000 + int(msg.header.stamp.nanosec)

            # Guard against invalid or zero timestamps.
            if stamp_ns <= 0:
                latency_ms = float('inf')
            else:
                latency_ns = max(0, now_ns - stamp_ns)
                latency_ms = latency_ns / 1e6

            threshold_ms = self._threshold_for_topic(topic)

            out = String()
            if latency_ms > threshold_ms:
                out.data = f'ALARM:{topic}:latency={latency_ms:.2f}ms'
            else:
                out.data = f'OK:{topic}:latency={latency_ms:.2f}ms'
            self._alarm_pub.publish(out)

        return _callback


def main(args=None) -> None:
    """Entry point for ros2 run monitoring latency_monitor."""
    rclpy.init(args=args)
    node = LatencyMonitorNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
