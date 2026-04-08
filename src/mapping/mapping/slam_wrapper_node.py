#!/usr/bin/env python3

"""SLAM wrapper node for a single namespaced robot.

This node performs three responsibilities:
1. Subscribes to namespaced sensor topics (scan + odom).
2. Relays those topics to dedicated relay topics that slam_toolbox can remap to.
3. Publishes a periodic heartbeat status for system health monitoring.

The node does not implement SLAM; it only forwards data and reports health.
"""

from typing import Optional

import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String


class SlamWrapperNode(Node):
    """Wraps namespaced robot sensor streams for slam_toolbox integration."""

    def __init__(self) -> None:
        super().__init__("slam_wrapper_node")

        # Declare the robot namespace identifier used to build topic names.
        self.declare_parameter("robot_id", "robot1")
        self._robot_id = self.get_parameter("robot_id").get_parameter_value().string_value

        # Build all topic names from the robot_id so the node can be reused
        # for robot1, robot2, and robot3 without code changes.
        scan_topic = f"/{self._robot_id}/scan"
        odom_topic = f"/{self._robot_id}/odom"

        # Relay topics are intentionally separated from raw topics so launch
        # files can remap slam_toolbox inputs to these stable relay endpoints.
        # Example slam_toolbox remaps:
        #   scan := /<robot_id>/slam/scan
        #   odom := /<robot_id>/slam/odom
        relay_scan_topic = f"/{self._robot_id}/slam/scan"
        relay_odom_topic = f"/{self._robot_id}/slam/odom"

        # Heartbeat topic is global under /mapping while preserving robot id.
        self._status_topic = f"/mapping/{self._robot_id}/slam_status"

        # Track last scan timestamp for watchdog-based health classification.
        self._last_scan_time: Optional[Time] = None
        self._scan_timeout_sec = 2.0

        # Publishers for relayed sensor streams consumed by slam_toolbox.
        self._scan_relay_pub = self.create_publisher(LaserScan, relay_scan_topic, qos_profile_sensor_data)
        self._odom_relay_pub = self.create_publisher(Odometry, relay_odom_topic, qos_profile_sensor_data)

        # Publisher for per-robot SLAM heartbeat status.
        self._status_pub = self.create_publisher(String, self._status_topic, 10)

        # Subscribe to incoming namespaced robot topics.
        self.create_subscription(LaserScan, scan_topic, self._scan_callback, qos_profile_sensor_data)
        self.create_subscription(Odometry, odom_topic, self._odom_callback, qos_profile_sensor_data)

        # Publish heartbeat at 1 Hz as required.
        self.create_timer(1.0, self._heartbeat_timer_callback)

        self.get_logger().info(
            f"SlamWrapperNode started for {self._robot_id}: "
            f"in(scan={scan_topic}, odom={odom_topic}) "
            f"relay(scan={relay_scan_topic}, odom={relay_odom_topic}) "
            f"status={self._status_topic}"
        )

    def _scan_callback(self, msg: LaserScan) -> None:
        """Relay scan data and refresh watchdog timestamp."""
        self._last_scan_time = self.get_clock().now()
        self._scan_relay_pub.publish(msg)

    def _odom_callback(self, msg: Odometry) -> None:
        """Relay odometry data for slam_toolbox odom input remapping."""
        self._odom_relay_pub.publish(msg)

    def _heartbeat_timer_callback(self) -> None:
        """Publish ACTIVE/DEGRADED based on scan watchdog timeout."""
        now = self.get_clock().now()

        # DEGRADED if no scan has ever arrived, or if the latest scan is stale.
        if self._last_scan_time is None:
            status_value = "DEGRADED"
        else:
            elapsed_sec = (now - self._last_scan_time).nanoseconds / 1e9
            status_value = "ACTIVE" if elapsed_sec <= self._scan_timeout_sec else "DEGRADED"

        status_msg = String()
        status_msg.data = status_value
        self._status_pub.publish(status_msg)


def main(args=None) -> None:
    """Entry point for ros2 run mapping slam_wrapper_node."""
    rclpy.init(args=args)
    node = SlamWrapperNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
