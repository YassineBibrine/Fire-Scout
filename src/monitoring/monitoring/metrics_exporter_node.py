#!/usr/bin/env python3

"""Aggregate monitoring alarms into a single system health JSON report."""

import json
from importlib import import_module
from typing import Any, Dict, List, Set, cast

import rclpy
from rcl_interfaces.msg import ParameterDescriptor, ParameterType
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String


_interfaces_msg = import_module('firescout_interfaces.msg')
FireSensorAlert = cast(Any, getattr(_interfaces_msg, 'FireSensorAlert'))


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
        self.declare_parameter(
            'monitored_topics',
            value=[''],
            descriptor=ParameterDescriptor(type=ParameterType.PARAMETER_STRING_ARRAY),
        )
        self._monitored_topics = {t for t in list(self.get_parameter('monitored_topics').value) if t}

        self.declare_parameter('robot_ids', ['robot1', 'robot2', 'robot3'])
        self.declare_parameter('hybrid_silence_timeout_sec', 5.0)
        robot_ids_value = self.get_parameter('robot_ids').value
        self._robot_ids = [
            str(robot_id) for robot_id in robot_ids_value
        ] if isinstance(robot_ids_value, list) else ['robot1', 'robot2', 'robot3']
        self._hybrid_silence_timeout_sec = float(
            self.get_parameter('hybrid_silence_timeout_sec').value
        )
        if self._hybrid_silence_timeout_sec <= 0.0:
            self._hybrid_silence_timeout_sec = 5.0
        self._startup_time_sec = self.get_clock().now().nanoseconds / 1e9

        # Track active alarms keyed by topic so stale values are replaced.
        self._active_rate_alarms: Dict[str, str] = {}
        self._active_latency_alarms: Dict[str, str] = {}
        self._last_fire_sensor_seen: Dict[str, float] = {}
        self._last_camera_seen: Dict[str, float] = {}
        self._hybrid_subscriptions: List[Any] = []

        self.create_subscription(String, '/monitoring/rate_alarm', self._on_rate_alarm, 10)
        self.create_subscription(String, '/monitoring/latency_alarm', self._on_latency_alarm, 10)
        for robot_id in self._robot_ids:
            self._hybrid_subscriptions.append(
                self.create_subscription(
                    FireSensorAlert,
                    f'/{robot_id}/fire_sensor_alert',
                    self._make_hybrid_seen_callback(self._last_fire_sensor_seen, robot_id),
                    10,
                )
            )
            self._hybrid_subscriptions.append(
                self.create_subscription(
                    Image,
                    f'/{robot_id}/camera/image_raw',
                    self._make_hybrid_seen_callback(self._last_camera_seen, robot_id),
                    10,
                )
            )

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

    def _make_hybrid_seen_callback(self, target: Dict[str, float], robot_id: str):
        """Record last-seen time for one hybrid liveness input."""

        def _callback(_msg) -> None:
            target[robot_id] = self.get_clock().now().nanoseconds / 1e9

        return _callback

    def _hybrid_silence_alarms(self) -> Dict[str, str]:
        """Return CRITICAL alarms for robots with both sensor and camera silent."""
        now_sec = self.get_clock().now().nanoseconds / 1e9
        alarms: Dict[str, str] = {}

        for robot_id in self._robot_ids:
            sensor_seen = self._last_fire_sensor_seen.get(robot_id)
            camera_seen = self._last_camera_seen.get(robot_id)
            startup_grace_elapsed = (
                now_sec - self._startup_time_sec > self._hybrid_silence_timeout_sec
            )
            sensor_silent = (
                (sensor_seen is None and startup_grace_elapsed)
                or (
                    sensor_seen is not None
                    and now_sec - sensor_seen > self._hybrid_silence_timeout_sec
                )
            )
            camera_silent = (
                (camera_seen is None and startup_grace_elapsed)
                or (
                    camera_seen is not None
                    and now_sec - camera_seen > self._hybrid_silence_timeout_sec
                )
            )

            if sensor_silent and camera_silent:
                alarms[robot_id] = (
                    f'CRITICAL:{robot_id}:hybrid_inputs_silent:'
                    f'timeout={self._hybrid_silence_timeout_sec:.1f}s'
                )

        return alarms

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
        hybrid_alarm_map = self._hybrid_silence_alarms()
        hybrid_alarm_list = sorted(hybrid_alarm_map.values())

        alarming_topics = (
            set(self._active_rate_alarms.keys())
            | set(self._active_latency_alarms.keys())
            | {f'/{robot_id}/hybrid_inputs' for robot_id in hybrid_alarm_map}
        )
        overall = self._compute_overall_state(alarming_topics)
        if hybrid_alarm_list:
            overall = 'CRITICAL'

        report = {
            'timestamp': self.get_clock().now().nanoseconds,
            'rate_alarms': rate_alarm_list,
            'latency_alarms': latency_alarm_list,
            'hybrid_silence_alarms': hybrid_alarm_list,
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
