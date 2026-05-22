import subprocess
import sys
import time
from typing import Optional

import pytest
pytest.importorskip('rclpy')
pytest.importorskip('sensor_msgs.msg')
pytest.importorskip('std_msgs.msg')
import rclpy
from rclpy.duration import Duration
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String


@pytest.fixture(scope='function')
def ros_context():
    """Initialize ROS with deterministic latency thresholds for this test."""
    rclpy.init()
    process = subprocess.Popen([
    sys.executable,
    '-m',
    'monitoring.latency_monitor_node',
    '--ros-args',
    '-p', 'monitored_topics:=["/monitoring/test/scan"]',
    '-p', 'scan_max_latency_ms:=200.0',
    ])
    # Allow monitor process to start and discover graph entities.
    time.sleep(1.5)
    try:
        yield
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        rclpy.shutdown()


def _wait_for_message_with_prefix(node, received, prefix: str, timeout_sec: float = 3.0) -> Optional[str]:
    """Wait until a captured latency message starts with the requested prefix."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.05)
        for payload in received:
            if payload.startswith(prefix):
                return payload
    return None


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


def _wait_for_subscriber(node, publisher, timeout_sec: float = 5.0) -> bool:
    """Block until the monitor subprocess has discovered our publisher."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if publisher.get_subscription_count() >= 1:
            return True
        rclpy.spin_once(node, timeout_sec=0.05)
    return publisher.get_subscription_count() >= 1


def _publish_until_received(
    helper,
    publisher,
    stamp_factory,
    received,
    prefix: str,
    timeout_sec: float = 5.0,
    publish_period_sec: float = 0.1,
) -> Optional[str]:
    """Publish scans repeatedly with refreshed stamps until matching reply arrives.

    Running this test in parallel with other ROS packages can delay the
    subprocess monitor's subscription discovery, so a single one-shot publish
    races with subscription creation. Repeating the publish while polling for
    the latency alarm makes the assertion deterministic under load.
    """
    deadline = time.time() + timeout_sec
    next_publish = 0.0
    while time.time() < deadline:
        now = time.time()
        if now >= next_publish:
            _publish_scan(helper, publisher, stamp_factory())
            next_publish = now + publish_period_sec
        rclpy.spin_once(helper, timeout_sec=0.05)
        for payload in received:
            if payload.startswith(prefix):
                return payload
    return None


def test_latency_alarm_old_and_fresh_scan(ros_context):
    """Verify stale header stamp triggers ALARM and fresh stamp triggers OK."""
    helper = rclpy.create_node('test_latency_alarm_helper')
    pub = helper.create_publisher(LaserScan, '/monitoring/test/scan', 10)
    received_messages = []

    # Keep a live subscriber during the entire test to avoid missing one-shot alarms.
    sub = helper.create_subscription(
        String,
        '/monitoring/latency_alarm',
        lambda msg: received_messages.append(msg.data),
        10,
    )

    try:
        # Wait until the monitor subprocess has actually subscribed; otherwise
        # the first published scan is dropped before discovery completes (this
        # was the source of the flaky failure when colcon ran every package's
        # tests in parallel).
        assert _wait_for_subscriber(helper, pub, timeout_sec=5.0), (
            'latency_monitor_node never discovered /monitoring/test/scan publisher'
        )

        # Publish a stale scan (1 second old) which exceeds 200 ms threshold.
        stale_result = _publish_until_received(
            helper,
            pub,
            lambda: (helper.get_clock().now() - Duration(seconds=1.0)).to_msg(),
            received_messages,
            'ALARM:/monitoring/test/scan:latency=',
            timeout_sec=5.0,
        )
        assert stale_result is not None, 'No latency message received for stale scan'
        assert stale_result.startswith('ALARM:/monitoring/test/scan:latency='), stale_result

        # Drop the stale ALARM messages so the next phase observes only fresh
        # results (otherwise an already-buffered ALARM could be misread as OK).
        received_messages.clear()

        # Publish a fresh scan stamped at current time; should be within threshold.
        fresh_result = _publish_until_received(
            helper,
            pub,
            lambda: helper.get_clock().now().to_msg(),
            received_messages,
            'OK:/monitoring/test/scan:latency=',
            timeout_sec=5.0,
        )
        assert fresh_result is not None, 'No latency message received for fresh scan'
        assert fresh_result.startswith('OK:/monitoring/test/scan:latency='), fresh_result
    finally:
        helper.destroy_subscription(sub)
        helper.destroy_node()
