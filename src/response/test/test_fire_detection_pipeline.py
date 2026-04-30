from importlib import import_module
import subprocess
import sys
import time

import pytest
pytest.importorskip('rclpy')
pytest.importorskip('firescout_interfaces.msg')
import rclpy
FireDetection = getattr(import_module('firescout_interfaces.msg'), 'FireDetection')
from rclpy.node import Node


@pytest.fixture(scope='function')
def ros_node():
    rclpy.init()
    node = Node('test_fire_detection_pipeline_node')
    process = subprocess.Popen([
        sys.executable,
        '-m',
        'response.fire_detection_node',
        '--ros-args',
        '-p',
        'publish_demo_detections:=true',
        '-p',
        'robot_id:=robot1',
    ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    time.sleep(1.0)
    if process.poll() is not None:
        output = process.stdout.read() if process.stdout else ''
        raise RuntimeError(f'fire_detection_node exited early:\n{output}')
    try:
        yield node
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


def _wait_for_detection(node: Node, received, timeout_sec: float = 8.0):
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
        if received:
            return received[0]
    return None


def test_fire_detection_pipeline(ros_node: Node):
    received = []

    subscription = ros_node.create_subscription(
        FireDetection,
        '/robot1/fire_detection',
        lambda msg: received.append(msg),
        10,
    )

    try:
        detection = _wait_for_detection(ros_node, received, timeout_sec=8.0)
        assert detection is not None, 'No FireDetection message received'
        assert detection.confidence > 0.0
        assert detection.robot_name == 'robot1'
    finally:
        ros_node.destroy_subscription(subscription)
