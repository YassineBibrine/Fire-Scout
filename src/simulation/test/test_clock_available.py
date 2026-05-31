import time

import pytest
pytest.importorskip('rclpy')
pytest.importorskip('rosgraph_msgs.msg')
import rclpy
from rclpy.node import Node
from rosgraph_msgs.msg import Clock


@pytest.fixture(scope='module')
def ros_node():
    rclpy.init()
    node = Node('test_clock_available_node')
    try:
        yield node
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


def _wait_for_topic_type(node, topic_name, expected_type, timeout_sec=4.0):
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
        for name, types in node.get_topic_names_and_types():
            if name == topic_name and expected_type in types:
                return True
    return False


def test_clock_available(ros_node):
    clock_pub = ros_node.create_publisher(Clock, '/clock', 10)
    clock_pub.publish(Clock())
    assert _wait_for_topic_type(ros_node, '/clock', 'rosgraph_msgs/msg/Clock')
