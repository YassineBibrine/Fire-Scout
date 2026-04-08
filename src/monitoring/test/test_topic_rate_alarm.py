import subprocess
import time

import pytest
import rclpy
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String


@pytest.fixture(scope='function')
def ros_context():
    """Initialize ROS with parameter overrides used by the rate monitor under test."""
    rclpy.init()
    process = subprocess.Popen([
        'ros2', 'run', 'monitoring', 'topic_rate_monitor',
        '--ros-args',
        '-p', 'window_sec:=2.0',
        '-p', 'check_rate_hz:=2.0',
        '-p', 'min_rate_ratio:=0.7',
        '-p', 'monitored_topics:=[/monitoring/test/scan]',
        '-p', 'expected_rates_hz:=[10.0]',
    ])
    # Allow monitor process to start and discover graph entities.
    time.sleep(1.5)
    try:
        yield
    finally:
        process.terminate()
        process.wait(timeout=5)
        rclpy.shutdown()


def _spin_for(node, duration_sec: float) -> None:
    """Spin a node for a fixed duration to process timers and subscriptions."""
    deadline = time.time() + duration_sec
    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.05)


def _wait_for_alarm_message(node, timeout_sec: float = 4.0) -> str:
    """Wait for one message from /monitoring/rate_alarm and return payload."""
    received = {'msg': None}

    def _cb(msg: String) -> None:
        received['msg'] = msg.data

    sub = node.create_subscription(String, '/monitoring/rate_alarm', _cb, 10)
    try:
        deadline = time.time() + timeout_sec
        while time.time() < deadline and received['msg'] is None:
            rclpy.spin_once(node, timeout_sec=0.05)
        return received['msg']
    finally:
        node.destroy_subscription(sub)


def _publish_scan_for_duration(pub_node, pub, hz: float, duration_sec: float) -> None:
    """Publish LaserScan messages at approximately hz for duration_sec."""
    period = 1.0 / hz
    deadline = time.time() + duration_sec
    msg = LaserScan()
    msg.angle_min = 0.0
    msg.angle_max = 1.0
    msg.angle_increment = 0.1
    msg.range_min = 0.12
    msg.range_max = 12.0
    msg.ranges = [1.0] * 10

    while time.time() < deadline:
        msg.header.stamp = pub_node.get_clock().now().to_msg()
        msg.header.frame_id = 'robot1/base_scan'
        pub.publish(msg)
        rclpy.spin_once(pub_node, timeout_sec=0.0)
        time.sleep(period)


def test_topic_rate_alarm_low_then_ok(ros_context):
    """Verify low publication rate produces ALARM and healthy rate produces OK."""
    helper = rclpy.create_node('test_topic_rate_alarm_helper')

    pub = helper.create_publisher(LaserScan, '/monitoring/test/scan', 10)

    try:
        # Allow discovery and initial timer cycle.
        _spin_for(helper, 0.5)

        # Publish too slowly (~1 Hz vs expected 10 Hz) to trigger ALARM.
        _publish_scan_for_duration(helper, pub, hz=1.0, duration_sec=2.2)
        alarm_payload = _wait_for_alarm_message(helper, timeout_sec=3.0)
        assert alarm_payload is not None, 'No message published on /monitoring/rate_alarm'
        assert alarm_payload.startswith('ALARM:/monitoring/test/scan:'), alarm_payload

        # Publish fast enough (>7 Hz threshold) so monitor reports OK.
        _publish_scan_for_duration(helper, pub, hz=12.0, duration_sec=2.2)

        ok_seen = False
        deadline = time.time() + 3.0
        while time.time() < deadline:
            payload = _wait_for_alarm_message(helper, timeout_sec=0.5)
            if payload == 'OK':
                ok_seen = True
                break

        assert ok_seen, 'Expected OK message on /monitoring/rate_alarm at healthy rate'
    finally:
        helper.destroy_node()
