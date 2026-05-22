#!/usr/bin/env python3

"""SLAM wrapper node for a single namespaced robot.

This node performs three responsibilities:
1. Subscribes to namespaced sensor topics (scan + odom).
2. Relays those topics to dedicated relay topics that slam_toolbox can remap to.
3. Publishes a periodic heartbeat status for system health monitoring.

The node does not implement SLAM; it only forwards data and reports health.
"""

import copy
from typing import Optional

import rclpy
from rclpy.executors import ExternalShutdownException
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
from rclpy.time import Time
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String
from tf2_msgs.msg import TFMessage


class SlamWrapperNode(Node):
    """Wraps namespaced robot sensor streams for slam_toolbox integration."""

    def __init__(self) -> None:
        super().__init__("slam_wrapper_node")

        # Declare the robot namespace identifier used to build topic names.
        self.declare_parameter("robot_id", "robot1")
        self.declare_parameter("use_global_lidar", False)
        self.declare_parameter("global_lidar_topic", "/lidar")
        self.declare_parameter("scan_relay_min_period_sec", 0.15)
        self.declare_parameter("odom_tf_publish_period_sec", 0.1)
        self._robot_id = self.get_parameter("robot_id").get_parameter_value().string_value
        self._use_global_lidar = self.get_parameter("use_global_lidar").get_parameter_value().bool_value
        self._global_lidar_topic = self.get_parameter("global_lidar_topic").get_parameter_value().string_value
        self._scan_relay_min_period_sec = max(
            float(self.get_parameter("scan_relay_min_period_sec").value),
            0.0,
        )
        self._odom_tf_publish_period_sec = max(
            float(self.get_parameter("odom_tf_publish_period_sec").value),
            0.02,
        )

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
        self._last_relayed_scan_time: Optional[Time] = None
        self._latest_odom: Optional[Odometry] = None
        self._scan_timeout_sec = 2.0

        # Publishers for relayed sensor streams consumed by slam_toolbox.
        reliable_qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
        odom_sub_qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        self._scan_relay_pub = self.create_publisher(LaserScan, relay_scan_topic, reliable_qos)
        self._odom_relay_pub = self.create_publisher(Odometry, relay_odom_topic, reliable_qos)
        self._tf_pub = self.create_publisher(TFMessage, "/tf", 100)

        # Publisher for per-robot SLAM heartbeat status.
        self._status_pub = self.create_publisher(String, self._status_topic, 10)

        # Subscribe to incoming scan topics. Prefer a single global lidar topic
        # (from Gazebo) when enabled, and filter by frame_id per robot.
        scan_sub_topic = self._global_lidar_topic if self._use_global_lidar else scan_topic
        self.create_subscription(LaserScan, scan_sub_topic, self._scan_callback, qos_profile_sensor_data)
        # Odom from ros_gz_bridge is best-effort; match it so we do not miss data.
        self.create_subscription(Odometry, odom_topic, self._odom_callback, odom_sub_qos)

        # Publish heartbeat at 1 Hz as required.
        self.create_timer(1.0, self._heartbeat_timer_callback)
        self.create_timer(self._odom_tf_publish_period_sec, self._odom_tf_timer_callback)

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
        now = self.get_clock().now()
        self._last_scan_time = now
        if self._last_relayed_scan_time is not None and self._scan_relay_min_period_sec > 0.0:
            elapsed_sec = (now - self._last_relayed_scan_time).nanoseconds / 1e9
            if elapsed_sec < self._scan_relay_min_period_sec:
                return
        self._last_relayed_scan_time = now
        # Gazebo produces sensor frame_id in various formats depending on
        # whether gz_frame_id is set: 'base_link', 'robot1/base_link',
        # 'robot1::base_link', or a full sensor-scoped frame. Normalize scans
        # to the robot-local lidar frame; slam_robot.launch.py publishes the
        # corresponding base_link -> lidar static transform.
        fixed_msg = copy.copy(msg)
        fixed_msg.header = copy.copy(msg.header)
        fixed_msg.header.stamp = now.to_msg()
        fixed_msg.header.frame_id = f'{self._robot_id}/lidar'
        if self._latest_odom is not None:
            odom_at_scan_time = copy.copy(self._latest_odom)
            odom_at_scan_time.header = copy.copy(self._latest_odom.header)
            odom_at_scan_time.header.stamp = fixed_msg.header.stamp
            self._publish_odom_tf(odom_at_scan_time)
        self._scan_relay_pub.publish(fixed_msg)

    def _odom_callback(self, msg: Odometry) -> None:
        """Relay odometry data and publish the matching odom -> base_link TF."""
        now = self.get_clock().now()
        fixed_msg = copy.copy(msg)
        fixed_msg.header = copy.copy(msg.header)
        # Set correct frame_id for slam_toolbox (expects robotX/odom)
        fixed_msg.header.frame_id = f'{self._robot_id}/odom'
        fixed_msg.header.stamp = now.to_msg()
        # Also set child_frame_id for base_link
        fixed_msg.child_frame_id = f'{self._robot_id}/base_link'
        self._latest_odom = fixed_msg
        self._odom_relay_pub.publish(fixed_msg)
        self._publish_odom_tf(fixed_msg)

    def _publish_odom_tf(self, odom: Odometry) -> None:
        """Publish the robot-local odom -> base_link TF for the given odom."""
        transform = TransformStamped()
        # Reuse the odom message's stamp so the TF stamp matches the /clock
        # timeline that Nav2 / SLAM are querying against. Stamping with an
        # independent get_clock().now() raced with /clock startup under
        # use_sim_time=true and could leave the TF buffer empty.
        transform.header.stamp = odom.header.stamp
        transform.header.frame_id = f'{self._robot_id}/odom'
        transform.child_frame_id = f'{self._robot_id}/base_link'
        transform.transform.translation.x = odom.pose.pose.position.x
        transform.transform.translation.y = odom.pose.pose.position.y
        transform.transform.translation.z = odom.pose.pose.position.z
        transform.transform.rotation = odom.pose.pose.orientation
        self._tf_pub.publish(TFMessage(transforms=[transform]))

    def _odom_tf_timer_callback(self) -> None:
        """Refresh the latest robot-local odom -> base_link TF."""
        if self._latest_odom is None:
            return
        odom = copy.copy(self._latest_odom)
        odom.header = copy.copy(self._latest_odom.header)
        odom.header.stamp = self.get_clock().now().to_msg()
        self._publish_odom_tf(odom)

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
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
