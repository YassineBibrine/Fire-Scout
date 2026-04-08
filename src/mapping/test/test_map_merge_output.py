import time

import pytest
import rclpy
from nav_msgs.msg import OccupancyGrid
from rclpy.node import Node
from std_msgs.msg import String


@pytest.fixture(scope='module')
def ros_node():
    """Create one ROS node used by all map merge output tests in this module."""
    rclpy.init()
    node = Node('test_map_merge_output_node')
    try:
        yield node
    finally:
        node.destroy_node()
        rclpy.shutdown()


def _wait_for_first_message(node: Node, topic_name: str, msg_type, timeout_sec: float = 8.0):
    """Subscribe to a topic and wait up to timeout_sec for the first message."""
    # Use a list so callback can mutate shared state from closure.
    received_messages = []

    # Capture each received message in-order for assertions.
    def _callback(msg) -> None:
        received_messages.append(msg)

    # Create temporary subscription used only for this wait helper.
    subscription = node.create_subscription(msg_type, topic_name, _callback, 10)

    # Spin the node until at least one message arrives or timeout is reached.
    end_time = time.time() + timeout_sec
    while time.time() < end_time and not received_messages:
        rclpy.spin_once(node, timeout_sec=0.1)

    # Clean up the temporary subscription before returning.
    node.destroy_subscription(subscription)

    if received_messages:
        return received_messages[0]
    return None


def test_merged_map_topic_publishes_occupancy_grid(ros_node: Node):
    """Verify /map publishes OccupancyGrid with valid metadata and map frame."""
    # Wait for one OccupancyGrid message from merged map topic.
    msg = _wait_for_first_message(ros_node, '/map', OccupancyGrid, timeout_sec=8.0)

    # Ensure at least one message was received within timeout.
    assert msg is not None, 'No nav_msgs/OccupancyGrid message received on /map within 8 seconds'

    # Validate merged map dimensions are non-empty.
    assert msg.info.width > 0, 'Merged map width must be greater than zero'
    assert msg.info.height > 0, 'Merged map height must be greater than zero'

    # Validate merged map frame follows global map frame contract.
    assert msg.header.frame_id == 'map', f'Expected frame_id "map", got "{msg.header.frame_id}"'


def test_map_merge_status_publishes_valid_string(ros_node: Node):
    """Verify map merge status topic publishes one of the allowed status values."""
    # Wait for one status String message from map merge status topic.
    msg = _wait_for_first_message(ros_node, '/mapping/map_merge_status', String, timeout_sec=8.0)

    # Ensure at least one status message was received within timeout.
    assert msg is not None, 'No std_msgs/String message received on /mapping/map_merge_status within 8 seconds'

    # Enforce exact allowed status contract.
    valid_values = {'ALL_READY', 'PARTIAL_1', 'PARTIAL_2', 'NO_MAPS'}
    assert msg.data in valid_values, f'Invalid map merge status value: {msg.data}'
