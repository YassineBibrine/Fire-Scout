import time

import pytest
pytest.importorskip('rclpy')
pytest.importorskip('nav_msgs.msg')
import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node


@pytest.fixture(scope='module')
def ros_node():
    rclpy.init()
    node = Node('test_spawn_namespaces_node')
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


def test_spawn_namespaces(ros_node):
    publishers = {
        robot_id: ros_node.create_publisher(Odometry, f'/{robot_id}/odom', 10)
        for robot_id in ('robot1', 'robot2', 'robot3')
    }
    for publisher in publishers.values():
        publisher.publish(Odometry())
    for robot_id in ('robot1', 'robot2', 'robot3'):
        assert _wait_for_topic_type(ros_node, f'/{robot_id}/odom', 'nav_msgs/msg/Odometry')
