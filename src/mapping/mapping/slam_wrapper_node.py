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
from rclpy.qos import QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
from rclpy.time import Time
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String


class SlamWrapperNode(Node):
    """Wraps namespaced robot sensor streams for slam_toolbox integration."""

    def __init__(self) -> None:
        super().__init__("slam_wrapper_node")

        # Declare the robot namespace identifier used to build topic names.
        self.declare_parameter("robot_id", "robot1")
        self.declare_parameter("use_global_lidar", False)
        self.declare_parameter("global_lidar_topic", "/lidar")
        self._robot_id = self.get_parameter("robot_id").get_parameter_value().string_value
        self._use_global_lidar = self.get_parameter("use_global_lidar").get_parameter_value().bool_value
        self._global_lidar_topic = self.get_parameter("global_lidar_topic").get_parameter_value().string_value

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
        reliable_qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
        self._scan_relay_pub = self.create_publisher(LaserScan, relay_scan_topic, reliable_qos)
        self._odom_relay_pub = self.create_publisher(Odometry, relay_odom_topic, reliable_qos)

        # Publisher for per-robot SLAM heartbeat status.
        self._status_pub = self.create_publisher(String, self._status_topic, 10)

        # Subscribe to incoming scan topics. Prefer a single global lidar topic
        # (from Gazebo) when enabled, and filter by frame_id per robot.
        scan_sub_topic = self._global_lidar_topic if self._use_global_lidar else scan_topic
        self.create_subscription(LaserScan, scan_sub_topic, self._scan_callback, qos_profile_sensor_data)
        self.create_subscription(Odometry, odom_topic, self._odom_callback, qos_profile_sensor_data)

        # Publish heartbeat at 1 Hz as required.
        self.create_timer(1.0, self._heartbeat_timer_callback)

        self.get_logger().info(
            f"SlamWrapperNode started for {self._robot_id}: "
            f"in(scan={scan_sub_topic}, odom={odom_topic}) "
            f"relay(scan={relay_scan_topic}, odom={relay_odom_topic}) "
            f"status={self._status_topic}"
        )

    def _is_robot_scan(self, frame_id: str) -> bool:
        """Return true if frame_id likely belongs to this robot."""
        if not frame_id:
            return False
        if frame_id.startswith(f"{self._robot_id}:"):
            return True
        if frame_id.startswith(f"{self._robot_id}/"):
            return True
        return f"{self._robot_id}::" in frame_id

    def _scan_callback(self, msg: LaserScan) -> None:
        """Relay scan data with corrected frame_id and refresh watchdog timestamp."""
        if self._use_global_lidar and not self._is_robot_scan(msg.header.frame_id):
            return
        self._last_scan_time = self.get_clock().now()
        # Gazebo produces sensor frame_id in various formats depending on
        # whether gz_frame_id is set: 'base_link', 'robot1/base_link', 'robot1::base_link'.
        # slam_toolbox requires exactly '{robot_id}/base_link' to resolve TF lookups.
        # We unconditionally force the correct namespaced frame_id here so the fix
        # is robust to any Gazebo sensor naming behavior.
        import copy
        fixed_msg = copy.copy(msg)
        fixed_msg.header = copy.copy(msg.header)
        fixed_msg.header.frame_id = f'{self._robot_id}/base_link'
        self._scan_relay_pub.publish(fixed_msg)

    def _odom_callback(self, msg: Odometry) -> None:
        """Relay odometry data for slam_toolbox odom input remapping."""
        # Set correct frame_id for slam_toolbox (expects robotX/odom)
        msg.header.frame_id = f'{self._robot_id}/odom'
        # Also set child_frame_id for base_link
        msg.child_frame_id = f'{self._robot_id}/base_link'
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
