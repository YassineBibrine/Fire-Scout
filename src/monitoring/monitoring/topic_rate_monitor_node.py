#!/usr/bin/env python3

"""Monitor topic publication rates and emit alarms when rates drop."""

from collections import deque
from typing import Callable, Deque, Dict, List, Tuple

import rclpy
from nav_msgs.msg import OccupancyGrid, Odometry
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String


class TopicRateMonitorNode(Node):
    """Tracks message rates over a 5-second window for configured topics."""

    def __init__(self) -> None:
        super().__init__('topic_rate_monitor_node')

        # Core monitoring controls.
        self.declare_parameter('window_sec', 5.0)
        self.declare_parameter('check_rate_hz', 2.0)
        self.declare_parameter('min_rate_ratio', 0.7)

        # Preferred parameter interface.
        self.declare_parameter('monitored_topics', [''])
        self.declare_parameter('expected_rates_hz', [0.0])

        # Backward-compatible fallback used by older config stubs.
        self.declare_parameter('topics', [''])
        self.declare_parameter('min_rate_hz', 0.0)

        self._window_sec = float(self.get_parameter('window_sec').value)
        self._check_rate_hz = float(self.get_parameter('check_rate_hz').value)
        self._min_rate_ratio = float(self.get_parameter('min_rate_ratio').value)

        if self._window_sec <= 0.0:
            self._window_sec = 5.0
        if self._check_rate_hz <= 0.0:
            self._check_rate_hz = 2.0
        if self._min_rate_ratio <= 0.0:
            self._min_rate_ratio = 0.7

        # Parse monitoring target topics and expected rates.
        topics, expected_rates = self._load_topic_configuration()
        self._expected_rates: Dict[str, float] = {
            topic: expected for topic, expected in zip(topics, expected_rates)
        }

        # Keep a rolling timestamp queue per topic for windowed rate estimation.
        self._arrival_times: Dict[str, Deque[float]] = {
            topic: deque() for topic in topics
        }

        # Publisher for rate health alarms.
        self._alarm_pub = self.create_publisher(String, '/monitoring/rate_alarm', 10)

        # Create subscriptions per topic using known Fire-Scout message types.
        self._subscriptions = []
        for topic in topics:
            msg_type = self._infer_msg_type(topic)
            callback = self._make_topic_callback(topic)
            self._subscriptions.append(self.create_subscription(msg_type, topic, callback, 10))

        # Evaluate all topic rates at 2 Hz (or configured value).
        self.create_timer(1.0 / self._check_rate_hz, self._check_all_topics)

        self.get_logger().info(
            f'TopicRateMonitorNode started with {len(topics)} topics, '
            f'window_sec={self._window_sec}, min_rate_ratio={self._min_rate_ratio}'
        )

    def _load_topic_configuration(self) -> Tuple[List[str], List[float]]:
        """Load monitored topics and expected rates from parameters."""
        monitored_topics = [t for t in list(self.get_parameter('monitored_topics').value) if t]
        expected_rates = list(self.get_parameter('expected_rates_hz').value)

        # Backward-compatible fallback: use `topics` and single min_rate_hz.
        if not monitored_topics:
            monitored_topics = [t for t in list(self.get_parameter('topics').value) if t]

        if not monitored_topics:
            self.get_logger().warn('No monitored topics configured; monitor will publish OK.')
            return [], []

        if expected_rates and len(expected_rates) == len(monitored_topics):
            cleaned_rates = [max(0.0, float(v)) for v in expected_rates]
            return monitored_topics, cleaned_rates

        fallback_rate = float(self.get_parameter('min_rate_hz').value)
        if fallback_rate <= 0.0:
            fallback_rate = 1.0

        self.get_logger().warn(
            'expected_rates_hz missing/mismatched; applying fallback expected rate '
            f'{fallback_rate} Hz for all monitored topics.'
        )
        return monitored_topics, [fallback_rate] * len(monitored_topics)

    def _infer_msg_type(self, topic: str):
        """Infer message class from topic naming convention used in Fire-Scout."""
        if topic.endswith('/scan'):
            return LaserScan
        if topic.endswith('/odom'):
            return Odometry
        if topic.endswith('/map') or topic == '/map':
            return OccupancyGrid
        if topic.endswith('_status'):
            return String

        # Default to String for monitoring custom status/event topics.
        return String

    def _make_topic_callback(self, topic: str) -> Callable:
        """Build callback that records message arrival times for one topic."""

        def _callback(_msg) -> None:
            now_sec = self.get_clock().now().nanoseconds / 1e9
            arrivals = self._arrival_times[topic]
            arrivals.append(now_sec)
            self._prune_old(arrivals, now_sec)

        return _callback

    def _prune_old(self, arrivals: Deque[float], now_sec: float) -> None:
        """Drop timestamps outside the sliding time window."""
        cutoff = now_sec - self._window_sec
        while arrivals and arrivals[0] < cutoff:
            arrivals.popleft()

    def _check_all_topics(self) -> None:
        """Compute per-topic rates and publish alarm or OK summary."""
        now_sec = self.get_clock().now().nanoseconds / 1e9
        alarms: List[str] = []

        for topic, expected_hz in self._expected_rates.items():
            arrivals = self._arrival_times[topic]
            self._prune_old(arrivals, now_sec)

            actual_hz = float(len(arrivals)) / self._window_sec
            min_allowed = expected_hz * self._min_rate_ratio

            if actual_hz < min_allowed:
                alarms.append(
                    f'ALARM:{topic}:expected={expected_hz:.2f}hz:actual={actual_hz:.2f}hz'
                )

        if alarms:
            for alarm in alarms:
                msg = String()
                msg.data = alarm
                self._alarm_pub.publish(msg)
        else:
            msg = String()
            msg.data = 'OK'
            self._alarm_pub.publish(msg)


def main(args=None) -> None:
    """Entry point for ros2 run monitoring topic_rate_monitor."""
    rclpy.init(args=args)
    node = TopicRateMonitorNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
