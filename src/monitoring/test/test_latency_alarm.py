import subprocess
import time

import pytest
import rclpy
from rclpy.duration import Duration
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String


@pytest.fixture(scope='function')
def ros_context():
    """Initialize ROS with deterministic latency thresholds for this test."""
    rclpy.init()
    process = subprocess.Popen([
        'ros2', 'run', 'monitoring', 'latency_monitor',
        '--ros-args',
        '-p', 'monitored_topics:=[/monitoring/test/scan]',
        '-p', 'scan_max_latency_ms:=200.0',
    ])
    # Allow monitor process to start and discover graph entities.
    time.sleep(1.5)
    try:
        yield
    finally:
        process.terminate()
        process.wait(timeout=5)
        rclpy.shutdown()


def _wait_for_message(node, timeout_sec: float = 3.0) -> str:
    """Wait for one latency status message and return its payload."""
    received = {'msg': None}

    def _cb(msg: String) -> None:
        received['msg'] = msg.data

    sub = node.create_subscription(String, '/monitoring/latency_alarm', _cb, 10)
    try:
        deadline = time.time() + timeout_sec
        while time.time() < deadline and received['msg'] is None:
            rclpy.spin_once(node, timeout_sec=0.05)
        return received['msg']
    finally:
        node.destroy_subscription(sub)


def _publish_scan(publisher_node, publisher, stamp_msg) -> None:
    """Publish a single minimal LaserScan message with provided stamp."""
    msg = LaserScan()
    msg.header.stamp = stamp_msg
    msg.header.frame_id = 'robot1/base_scan'
    msg.angle_min = 0.0
    msg.angle_max = 1.0
    msg.angle_increment = 0.1
    msg.range_min = 0.12
    msg.range_max = 12.0
    msg.ranges = [1.0] * 10
    publisher.publish(msg)
    rclpy.spin_once(publisher_node, timeout_sec=0.0)


def test_latency_alarm_old_and_fresh_scan(ros_context):
    """Verify stale header stamp triggers ALARM and fresh stamp triggers OK."""
    helper = rclpy.create_node('test_latency_alarm_helper')
    pub = helper.create_publisher(LaserScan, '/monitoring/test/scan', 10)

    try:
        # Give ROS graph a moment for discovery.
        start_deadline = time.time() + 0.5
        while time.time() < start_deadline:
            rclpy.spin_once(helper, timeout_sec=0.05)

        # Publish a stale scan (1 second old) which exceeds 200 ms threshold.
        stale_stamp = (helper.get_clock().now() - Duration(seconds=1.0)).to_msg()
        _publish_scan(helper, pub, stale_stamp)
        stale_result = _wait_for_message(helper, timeout_sec=2.0)
        assert stale_result is not None, 'No latency message received for stale scan'
        assert stale_result.startswith('ALARM:/monitoring/test/scan:latency='), stale_result

        # Publish a fresh scan stamped at current time; should be within threshold.
        fresh_stamp = helper.get_clock().now().to_msg()
        _publish_scan(helper, pub, fresh_stamp)
        fresh_result = _wait_for_message(helper, timeout_sec=2.0)
        assert fresh_result is not None, 'No latency message received for fresh scan'
        assert fresh_result.startswith('OK:/monitoring/test/scan:latency='), fresh_result
    finally:
        helper.destroy_node()
