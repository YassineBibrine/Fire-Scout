#!/usr/bin/env python3

"""Demultiplex global /lidar scans into per-robot /<robot_id>/scan topics."""

from typing import Dict, List, Optional

import rclpy
from rclpy.node import Node
from rclpy.publisher import Publisher
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan


class LidarDemuxNode(Node):
    """Routes shared lidar scans to robot-specific scan topics based on frame_id."""

    def __init__(self) -> None:
        super().__init__("lidar_demux_node")

        self.declare_parameter("use_sim_time", True)
        self.declare_parameter("robot_ids", ["robot1", "robot2", "robot3"])
        self.declare_parameter("input_topic", "/lidar")

        robot_ids_param = self.get_parameter("robot_ids").get_parameter_value().string_array_value
        self._robot_ids: List[str] = list(robot_ids_param) if robot_ids_param else ["robot1", "robot2", "robot3"]

        input_topic = self.get_parameter("input_topic").get_parameter_value().string_value
        self._input_topic = input_topic if input_topic else "/lidar"

        self._publishers: Dict[str, Publisher] = {}
        for robot_id in self._robot_ids:
            self._publishers[robot_id] = self.create_publisher(
                LaserScan,
                f"/{robot_id}/scan",
                qos_profile_sensor_data,
            )

        self.create_subscription(
            LaserScan,
            self._input_topic,
            self._scan_callback,
            qos_profile_sensor_data,
        )

        self._last_unknown_warn_time = self.get_clock().now()
        self._unknown_warn_interval_ns = int(5e9)

        self.get_logger().info(
            f"LidarDemuxNode listening on {self._input_topic} and publishing to {self._robot_ids}"
        )

    def _extract_robot_id(self, frame_id: str) -> Optional[str]:
        if not frame_id:
            return None
        robot_id = frame_id.split("::", 1)[0]
        robot_id = robot_id.split("/", 1)[0]
        if robot_id in self._robot_ids:
            return robot_id
        return None

    def _scan_callback(self, msg: LaserScan) -> None:
        robot_id = self._extract_robot_id(msg.header.frame_id)
        if robot_id is None:
            now = self.get_clock().now()
            if (now - self._last_unknown_warn_time).nanoseconds > self._unknown_warn_interval_ns:
                self.get_logger().warn(
                    "Unable to route /lidar scan: unknown frame_id "
                    f"'{msg.header.frame_id}'. Expected one of {self._robot_ids}."
                )
                self._last_unknown_warn_time = now
            return

        publisher = self._publishers.get(robot_id)
        if publisher is None:
            return
        publisher.publish(msg)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = LidarDemuxNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
