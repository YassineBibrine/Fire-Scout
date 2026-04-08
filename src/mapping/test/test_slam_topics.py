import time

import pytest
import rclpy
from rclpy.node import Node


@pytest.fixture(scope='module')
def ros_node():
    """Create one ROS node for graph introspection in this test module."""
    rclpy.init()
    node = Node('test_slam_topics_node')
    try:
        yield node
    finally:
        node.destroy_node()
        rclpy.shutdown()


def _wait_for_topic_type(node: Node, topic_name: str, expected_type: str, timeout_sec: float = 8.0) -> bool:
    """Wait until the ROS graph reports topic_name with expected_type."""
    end_time = time.time() + timeout_sec
    while time.time() < end_time:
        # Spin to process graph events and discovery updates.
        rclpy.spin_once(node, timeout_sec=0.1)
        for name, types in node.get_topic_names_and_types():
            if name == topic_name and expected_type in types:
                return True
    return False


def test_robot_map_topics_publish_occupancy_grid(ros_node: Node):
    """Verify each robot map topic exists with nav_msgs/msg/OccupancyGrid type."""
    expected_type = 'nav_msgs/msg/OccupancyGrid'
    for robot in ('robot1', 'robot2', 'robot3'):
        topic = f'/{robot}/map'
        assert _wait_for_topic_type(ros_node, topic, expected_type), (
            f'Missing or wrong type for topic {topic}; expected {expected_type}'
        )


def test_slam_status_topics_publish_string(ros_node: Node):
    """Verify per-robot SLAM status heartbeat topics use std_msgs/msg/String."""
    expected_type = 'std_msgs/msg/String'
    for robot in ('robot1', 'robot2', 'robot3'):
        topic = f'/mapping/{robot}/slam_status'
        assert _wait_for_topic_type(ros_node, topic, expected_type), (
            f'Missing or wrong type for topic {topic}; expected {expected_type}'
        )
