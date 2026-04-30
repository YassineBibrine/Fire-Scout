import time

import pytest
pytest.importorskip('rclpy')
pytest.importorskip('sensor_msgs.msg')
pytest.importorskip('nav_msgs.msg')
pytest.importorskip('tf2_msgs.msg')
import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from tf2_msgs.msg import TFMessage


def _wait_for_topic_type(node: Node, topic_name: str, expected_type: str, timeout_sec: float = 4.0) -> bool:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
        for name, types in node.get_topic_names_and_types():
            if name == topic_name and expected_type in types:
                return True
    return False


def test_bridge_topics():
    rclpy.init()
    node = Node('test_bridge_topics_node')
    try:
        scan_pub = node.create_publisher(LaserScan, '/robot1/scan', 10)
        odom_pub = node.create_publisher(Odometry, '/robot1/odom', 10)
        tf_pub = node.create_publisher(TFMessage, '/tf', 10)

        scan_pub.publish(LaserScan())
        odom_pub.publish(Odometry())
        tf_pub.publish(TFMessage())

        assert _wait_for_topic_type(node, '/robot1/scan', 'sensor_msgs/msg/LaserScan')
        assert _wait_for_topic_type(node, '/robot1/odom', 'nav_msgs/msg/Odometry')
        assert _wait_for_topic_type(node, '/tf', 'tf2_msgs/msg/TFMessage')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
