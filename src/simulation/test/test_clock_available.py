import time

import pytest
pytest.importorskip('rclpy')
pytest.importorskip('rosgraph_msgs.msg')
import rclpy
from rclpy.node import Node
from rosgraph_msgs.msg import Clock


def _wait_for_topic_type(node: Node, topic_name: str, expected_type: str, timeout_sec: float = 4.0) -> bool:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
        for name, types in node.get_topic_names_and_types():
            if name == topic_name and expected_type in types:
                return True
    return False


def test_clock_available():
    rclpy.init()
    node = Node('test_clock_available_node')
    try:
        clock_pub = node.create_publisher(Clock, '/clock', 10)
        clock_pub.publish(Clock())
        assert _wait_for_topic_type(node, '/clock', 'rosgraph_msgs/msg/Clock')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
