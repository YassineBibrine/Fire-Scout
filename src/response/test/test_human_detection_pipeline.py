from importlib import import_module
import os
import subprocess
import sys
import time

import pytest
pytest.importorskip('rclpy')
pytest.importorskip('firescout_interfaces.msg')
import rclpy
HumanDetection = getattr(import_module('firescout_interfaces.msg'), 'HumanDetection')
from rclpy.node import Node


@pytest.fixture(scope='function')
def ros_node():
    original_domain = os.environ.get('ROS_DOMAIN_ID')
    os.environ['ROS_DOMAIN_ID'] = '85'
    rclpy.init()
    node = Node('test_human_detection_pipeline_node')
    process = subprocess.Popen([
        sys.executable,
        '-m',
        'response.human_detection_node',
        '--ros-args',
        '-p',
        'publish_demo_detections:=true',
        '-p',
        'robot_id:=robot1',
        '-p',
        'use_sim_time:=false',
    ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    time.sleep(1.0)
    if process.poll() is not None:
        output = process.stdout.read() if process.stdout else ''
        raise RuntimeError(f'human_detection_node exited early:\n{output}')
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
        if original_domain is None:
            os.environ.pop('ROS_DOMAIN_ID', None)
        else:
            os.environ['ROS_DOMAIN_ID'] = original_domain


def _wait_for_detection(node: Node, received, timeout_sec: float = 8.0):
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
        if received:
            return received[0]
    return None


def test_human_detection_pipeline(ros_node: Node):
    received = []

    subscription = ros_node.create_subscription(
        HumanDetection,
        '/robot1/human_detection',
        lambda msg: received.append(msg),
        10,
    )

    try:
        detection = _wait_for_detection(ros_node, received, timeout_sec=8.0)
        assert detection is not None, 'No HumanDetection message received'
        assert detection.confidence > 0.0
        assert detection.robot_name == 'robot1'
    finally:
        ros_node.destroy_subscription(subscription)
