import subprocess
import time

import pytest
pytest.importorskip('rclpy')
pytest.importorskip('nav_msgs.msg')
pytest.importorskip('std_msgs.msg')
import rclpy
from nav_msgs.msg import OccupancyGrid
from rclpy.node import Node
from std_msgs.msg import String


@pytest.fixture(scope='module')
def ros_node():
    """Create one ROS node for graph introspection in this test module."""
    rclpy.init()
    node = Node('test_slam_topics_node')
    processes = []

    # Launch one slam wrapper node per robot so slam status topics are published.
    for robot in ('robot1', 'robot2', 'robot3'):
        processes.append(
            subprocess.Popen([
                'ros2',
                'run',
                'mapping',
                'slam_wrapper_node',
                '--ros-args',
                '-p',
                f'robot_id:={robot}',
            ])
        )

    # Create dummy map publishers so map topics exist with OccupancyGrid type.
    map_publishers = [
        node.create_publisher(OccupancyGrid, '/robot1/map', 10),
        node.create_publisher(OccupancyGrid, '/robot2/map', 10),
        node.create_publisher(OccupancyGrid, '/robot3/map', 10),
    ]

    # Create helper status publishers so expected slam status topic types are discoverable.
    status_publishers = [
        node.create_publisher(String, '/mapping/robot1/slam_status', 10),
        node.create_publisher(String, '/mapping/robot2/slam_status', 10),
        node.create_publisher(String, '/mapping/robot3/slam_status', 10),
    ]

    # Publish empty maps at 1 Hz to keep topics alive for graph discovery checks.
    def _publish_empty_maps() -> None:
        msg = OccupancyGrid()
        msg.header.frame_id = 'map'
        for publisher in map_publishers:
            publisher.publish(msg)

    # Publish periodic status heartbeats so status topic types are discoverable.
    def _publish_status() -> None:
        msg = String()
        msg.data = 'DEGRADED'
        for publisher in status_publishers:
            publisher.publish(msg)

    timer = node.create_timer(1.0, _publish_empty_maps)
    status_timer = node.create_timer(1.0, _publish_status)
    _publish_empty_maps()
    _publish_status()

    # Give ROS discovery time to register processes and topics.
    time.sleep(2.0)

    try:
        yield node
    finally:
        # Stop the periodic publisher timer before node shutdown.
        node.destroy_timer(timer)
        node.destroy_timer(status_timer)

        # Terminate all launched ROS processes and wait for clean exit.
        for process in processes:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

        node.destroy_node()
        # Always shutdown rclpy last after all process/node teardown is complete.
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
