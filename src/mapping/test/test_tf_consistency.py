import time

import pytest
import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from tf2_ros import Buffer, TransformListener


@pytest.fixture(scope='module')
def tf_context():
    """Create a ROS node with TF buffer/listener for transform availability checks."""
    rclpy.init()
    node = Node('test_tf_consistency_node')
    buffer = Buffer(cache_time=Duration(seconds=10.0))
    listener = TransformListener(buffer, node, spin_thread=False)
    try:
        yield node, buffer, listener
    finally:
        node.destroy_node()
        rclpy.shutdown()


def _wait_for_transform(node: Node, tf_buffer: Buffer, target: str, source: str, timeout_sec: float = 10.0) -> bool:
    """Wait until target<-source transform is available and lookup succeeds."""
    deadline = time.time() + timeout_sec

    while time.time() < deadline:
        # Spin the node so the TF listener can receive /tf and /tf_static.
        rclpy.spin_once(node, timeout_sec=0.1)

        try:
            if tf_buffer.can_transform(target, source, rclpy.time.Time(), timeout=Duration(seconds=0.1)):
                tf_buffer.lookup_transform(target, source, rclpy.time.Time(), timeout=Duration(seconds=0.1))
                return True
        except Exception:
            # Continue waiting until timeout if TF tree is still converging.
            pass

    return False


def test_required_tf_links_exist(tf_context):
    """Verify mandatory map-chain transforms for all three robots are available."""
    node, tf_buffer, _listener = tf_context

    for robot in ('robot1', 'robot2', 'robot3'):
        # Required global to namespaced map bridge.
        assert _wait_for_transform(node, tf_buffer, 'map', f'{robot}/map'), (
            f'Missing TF transform map <- {robot}/map'
        )

        # Required SLAM map to odom correction transform.
        assert _wait_for_transform(node, tf_buffer, f'{robot}/map', f'{robot}/odom'), (
            f'Missing TF transform {robot}/map <- {robot}/odom'
        )


def test_tf_lookup_no_exceptions_for_all_robots(tf_context):
    """Verify TF lookups complete for all robots without runtime exceptions."""
    node, tf_buffer, _listener = tf_context

    for robot in ('robot1', 'robot2', 'robot3'):
        assert _wait_for_transform(node, tf_buffer, 'map', f'{robot}/map')
        assert _wait_for_transform(node, tf_buffer, f'{robot}/map', f'{robot}/odom')
