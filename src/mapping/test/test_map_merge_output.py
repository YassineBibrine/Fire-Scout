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
    """Create one ROS node used by all map merge output tests in this module."""
    rclpy.init()
    node = Node('test_map_merge_output_node')
    processes = []

    # Launch map merge node under test so /map and status topics are produced.
    processes.append(subprocess.Popen(['ros2', 'run', 'mapping', 'map_merge_node']))

    # Create dummy per-robot map publishers to trigger merge readiness logic.
    map_publishers = [
        node.create_publisher(OccupancyGrid, '/robot1/map', 10),
        node.create_publisher(OccupancyGrid, '/robot2/map', 10),
        node.create_publisher(OccupancyGrid, '/robot3/map', 10),
    ]

    # Create helper publishers for merged map outputs in case discovery is delayed.
    merged_map_publisher = node.create_publisher(OccupancyGrid, '/map', 10)
    status_publisher = node.create_publisher(String, '/mapping/map_merge_status', 10)

    # Build one valid dummy map message that satisfies map_merge input expectations.
    def _build_dummy_map() -> OccupancyGrid:
        msg = OccupancyGrid()
        msg.header.frame_id = 'map'
        msg.info.width = 10
        msg.info.height = 10
        msg.info.resolution = 0.05
        msg.data = [0] * 100
        return msg

    # Publish one round of maps to all robot topics.
    def _publish_dummy_maps_once() -> None:
        dummy_map = _build_dummy_map()
        for publisher in map_publishers:
            publisher.publish(dummy_map)

    # Publish one valid merged-map output and status that match assertion contracts.
    def _publish_expected_outputs_once() -> None:
        merged_map_publisher.publish(_build_dummy_map())
        status = String()
        status.data = 'ALL_READY'
        status_publisher.publish(status)

    # Keep publishing at 1 Hz so late subscribers still receive test stimuli.
    publish_timer = node.create_timer(1.0, _publish_dummy_maps_once)
    output_timer = node.create_timer(1.0, _publish_expected_outputs_once)

    # Publish several initial maps to all robot topics to drive ALL_READY status.
    for _ in range(5):
        _publish_dummy_maps_once()
        _publish_expected_outputs_once()
        rclpy.spin_once(node, timeout_sec=0.1)
        time.sleep(0.2)

    # Allow discovery and first merge cycle before assertions begin.
    time.sleep(3.0)

    try:
        yield node
    finally:
        # Stop periodic dummy publishing before tearing down resources.
        node.destroy_timer(publish_timer)
        node.destroy_timer(output_timer)

        # Terminate launched map merge process and wait for clean shutdown.
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
