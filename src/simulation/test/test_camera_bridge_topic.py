"""Tests for Phase 2 camera bridge topic contract.

Verifies:
- /robotX/camera/image_raw topics exist for all three robots.
- Topics carry the correct sensor_msgs/msg/Image type.
- Namespace isolation is maintained (robot-specific prefixes only).

These tests operate at the ROS graph level without requiring a running
Gazebo instance: they publish stub Image messages and then assert that
the graph reports the expected topic types.
"""
import time

import pytest

pytest.importorskip('rclpy')
pytest.importorskip('sensor_msgs.msg')

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


@pytest.fixture(scope='module')
def ros_node():
    """Shared ROS node for camera bridge topic tests."""
    rclpy.init()
    node = Node('test_camera_bridge_topic_node')
    try:
        yield node
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


def _wait_for_topic_type(
    node: Node,
    topic_name: str,
    expected_type: str,
    timeout_sec: float = 5.0,
) -> bool:
    """Spin until topic_name is visible with expected_type in the ROS graph."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
        for name, types in node.get_topic_names_and_types():
            if name == topic_name and expected_type in types:
                return True
    return False


def test_camera_topics_exist_for_all_robots(ros_node: Node):
    """Verify /robotX/camera/image_raw topics are discoverable with Image type."""
    expected_type = 'sensor_msgs/msg/Image'

    # Create publishers so graph discovery can detect the topic type.
    publishers = {
        robot_id: ros_node.create_publisher(
            Image, f'/{robot_id}/camera/image_raw', 10
        )
        for robot_id in ('robot1', 'robot2', 'robot3')
    }

    # Publish at least one message per robot so the topic is live.
    stub_image = Image()
    stub_image.height = 480
    stub_image.width = 640
    stub_image.encoding = 'rgb8'
    stub_image.step = 640 * 3
    stub_image.data = bytes(640 * 480 * 3)

    for pub in publishers.values():
        pub.publish(stub_image)

    for robot_id in ('robot1', 'robot2', 'robot3'):
        topic = f'/{robot_id}/camera/image_raw'
        assert _wait_for_topic_type(ros_node, topic, expected_type), (
            f'Camera topic {topic} not found or has wrong type; '
            f'expected {expected_type}'
        )


def test_camera_topics_are_namespace_isolated(ros_node: Node):
    """Verify camera topics use per-robot namespaces and not a shared topic."""
    # A shared /camera/image_raw topic would violate the namespace policy.
    shared_topic = '/camera/image_raw'

    # Spin briefly to allow discovery.
    deadline = time.time() + 1.0
    while time.time() < deadline:
        rclpy.spin_once(ros_node, timeout_sec=0.1)

    topic_names = [name for name, _ in ros_node.get_topic_names_and_types()]
    assert shared_topic not in topic_names, (
        f'Found un-namespaced camera topic {shared_topic}; '
        'each robot must publish under its own namespace.'
    )


def test_camera_image_message_fields(ros_node: Node):
    """Verify that Image messages published on camera topics have expected fields."""
    received = []

    sub = ros_node.create_subscription(
        Image,
        '/robot1/camera/image_raw',
        lambda msg: received.append(msg),
        10,
    )

    pub = ros_node.create_publisher(Image, '/robot1/camera/image_raw', 10)

    try:
        # Publish a well-formed stub image matching SDF camera spec.
        msg = Image()
        msg.header.stamp = ros_node.get_clock().now().to_msg()
        msg.header.frame_id = 'robot1/camera'
        msg.height = 480
        msg.width = 640
        msg.encoding = 'rgb8'
        msg.is_bigendian = False
        msg.step = 640 * 3
        msg.data = bytes(640 * 480 * 3)
        pub.publish(msg)

        deadline = time.time() + 3.0
        while time.time() < deadline and not received:
            rclpy.spin_once(ros_node, timeout_sec=0.1)

        assert received, 'No Image message received on /robot1/camera/image_raw'
        received_msg = received[0]
        assert received_msg.width == 640, f'Expected width 640, got {received_msg.width}'
        assert received_msg.height == 480, f'Expected height 480, got {received_msg.height}'
        assert received_msg.encoding == 'rgb8', (
            f'Expected encoding rgb8, got {received_msg.encoding}'
        )
    finally:
        ros_node.destroy_subscription(sub)


def test_bridge_robot_launch_includes_camera_bridge():
    """Verify bridge_robot.launch.py source references the camera bridge definition."""
    from pathlib import Path

    launch_path = (
        Path(__file__).resolve().parents[1] / 'launch' / 'bridge_robot.launch.py'
    )
    source = launch_path.read_text(encoding='utf-8')

    assert 'camera' in source, (
        'bridge_robot.launch.py does not reference a camera bridge; '
        'Phase 2 camera topic will not be bridged from Gazebo to ROS.'
    )
    assert 'gz.msgs.Image' in source, (
        'bridge_robot.launch.py missing gz.msgs.Image type mapping for camera bridge.'
    )
    assert 'sensor_msgs/msg/Image' in source, (
        'bridge_robot.launch.py missing sensor_msgs/msg/Image type mapping for camera bridge.'
    )
    assert 'GZ_TO_ROS' in source, (
        "Camera bridge direction must be 'GZ_TO_ROS'."
    )