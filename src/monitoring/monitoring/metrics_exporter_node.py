#!/usr/bin/env python3

"""Aggregate monitoring alarms into a single system health JSON report."""

import json
from typing import Dict, Set

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MetricsExporterNode(Node):
    """Builds a consolidated health report from rate and latency alarm streams."""

    def __init__(self) -> None:
        super().__init__('metrics_exporter_node')

        # Publish system health at fixed cadence.
        self.declare_parameter('publish_rate_hz', 1.0)
        publish_rate_hz = float(self.get_parameter('publish_rate_hz').value)
        if publish_rate_hz <= 0.0:
            publish_rate_hz = 1.0

        # Optional expected topics list used to compute alarm ratio robustly.
        self.declare_parameter('monitored_topics', [])
        self._monitored_topics = set(list(self.get_parameter('monitored_topics').value))

        # Track active alarms keyed by topic so stale values are replaced.
        self._active_rate_alarms: Dict[str, str] = {}
        self._active_latency_alarms: Dict[str, str] = {}

        self.create_subscription(String, '/monitoring/rate_alarm', self._on_rate_alarm, 10)
        self.create_subscription(String, '/monitoring/latency_alarm', self._on_latency_alarm, 10)

        self._health_pub = self.create_publisher(String, '/monitoring/system_health', 10)
        self.create_timer(1.0 / publish_rate_hz, self._publish_health)

        self.get_logger().info('MetricsExporterNode started.')

    def _parse_topic_from_payload(self, payload: str) -> str:
        """Extract monitored topic from message format ALARM:<topic>:... or OK:<topic>:..."""
        parts = payload.split(':')
        if len(parts) >= 3:
            return parts[1]
        return ''

    def _on_rate_alarm(self, msg: String) -> None:
        """Update rate alarm state from incoming status message."""
        payload = msg.data.strip()
        topic = self._parse_topic_from_payload(payload)

        if payload == 'OK':
            # Global OK means all tracked rate alarms are cleared.
            self._active_rate_alarms.clear()
            return

        if payload.startswith('ALARM:') and topic:
            self._active_rate_alarms[topic] = payload
            return

        if payload.startswith('OK:') and topic:
            self._active_rate_alarms.pop(topic, None)

    def _on_latency_alarm(self, msg: String) -> None:
        """Update latency alarm state from incoming status message."""
        payload = msg.data.strip()
        topic = self._parse_topic_from_payload(payload)

        if payload.startswith('ALARM:') and topic:
            self._active_latency_alarms[topic] = payload
            return

        if payload.startswith('OK:') and topic:
            self._active_latency_alarms.pop(topic, None)

    def _compute_overall_state(self, alarming_topics: Set[str]) -> str:
        """Compute HEALTHY/DEGRADED/CRITICAL using the required ratio policy."""
        if not alarming_topics:
            return 'HEALTHY'

        # If monitored topic inventory is available, use it as denominator.
        if self._monitored_topics:
            denominator = max(1, len(self._monitored_topics))
            ratio = float(len(alarming_topics)) / float(denominator)
        else:
            # Without full inventory, fall back to a bounded estimate where each
            # active alarm represents one monitored topic.
            denominator = max(1, len(alarming_topics))
            ratio = float(len(alarming_topics)) / float(denominator)

        return 'CRITICAL' if ratio >= 0.5 else 'DEGRADED'

    def _publish_health(self) -> None:
        """Publish consolidated JSON report on /monitoring/system_health."""
        rate_alarm_list = sorted(self._active_rate_alarms.values())
        latency_alarm_list = sorted(self._active_latency_alarms.values())

        alarming_topics = set(self._active_rate_alarms.keys()) | set(self._active_latency_alarms.keys())
        overall = self._compute_overall_state(alarming_topics)

        report = {
            'timestamp': self.get_clock().now().nanoseconds,
            'rate_alarms': rate_alarm_list,
            'latency_alarms': latency_alarm_list,
            'overall': overall,
        }

        out = String()
        out.data = json.dumps(report, separators=(',', ':'))
        self._health_pub.publish(out)


def main(args=None) -> None:
    """Entry point for ros2 run monitoring metrics_exporter."""
    rclpy.init(args=args)
    node = MetricsExporterNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
