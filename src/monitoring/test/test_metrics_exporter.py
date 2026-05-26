import json
import subprocess
import sys
import time
from typing import Optional

import pytest

pytest.importorskip('rclpy')
pytest.importorskip('std_msgs.msg')

import rclpy
from std_msgs.msg import String


@pytest.fixture(scope='function')
def ros_context():
    rclpy.init()
    process = subprocess.Popen([
        sys.executable,
        '-m',
        'monitoring.metrics_exporter_node',
        '--ros-args',
        '-p', 'publish_rate_hz:=10.0',
        '-p', 'robot_ids:=[robot1]',
        '-p', 'hybrid_silence_timeout_sec:=0.25',
        '-p', 'monitored_topics:=[/robot1/fire_sensor_alert,/robot1/camera/image_raw]',
    ])
    time.sleep(0.5)
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


def _wait_for_report(node, received, timeout_sec: float = 3.0) -> Optional[dict]:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.05)
        for payload in received:
            report = json.loads(payload)
            if report.get('hybrid_silence_alarms'):
                return report
    return None


def test_metrics_exporter_critical_when_sensor_and_camera_silent(ros_context):
    helper = rclpy.create_node('test_metrics_exporter_helper')
    received = []
    sub = helper.create_subscription(
        String,
        '/monitoring/system_health',
        lambda msg: received.append(msg.data),
        10,
    )

    try:
        report = _wait_for_report(helper, received)
        assert report is not None, 'No hybrid silence report received'
        assert report['overall'] == 'CRITICAL'
        assert report['hybrid_silence_alarms'] == [
            'CRITICAL:robot1:hybrid_inputs_silent:timeout=0.2s'
        ]
    finally:
        helper.destroy_subscription(sub)
        helper.destroy_node()
