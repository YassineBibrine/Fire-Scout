from importlib import import_module
import os
import subprocess
import sys
import time

import pytest
pytest.importorskip('rclpy')
pytest.importorskip('firescout_interfaces.msg')
import rclpy
NodeStatus = getattr(import_module('firescout_interfaces.msg'), 'NodeStatus')
RobotHealth = getattr(import_module('firescout_interfaces.msg'), 'RobotHealth')
from rclpy.node import Node


@pytest.fixture(scope='function')
def ros_node():
    """Start health monitor node and provide a helper ROS node."""
    original_domain = os.environ.get('ROS_DOMAIN_ID')
    os.environ['ROS_DOMAIN_ID'] = '81'
    process = None
    node = None
    try:
        rclpy.init()
        node = Node('test_heartbeat_timeout_node')
        env = os.environ.copy()
        process = subprocess.Popen(
            [
                sys.executable,
                '-m',
                'coordination.health_monitor_node',
                '--ros-args',
                '-p',
                'use_sim_time:=false',
            ],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        time.sleep(2.5)
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ''
            raise RuntimeError(f'health_monitor_node exited early:\n{output}')
        yield node
    finally:
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        if original_domain is None:
            os.environ.pop('ROS_DOMAIN_ID', None)
        else:
            os.environ['ROS_DOMAIN_ID'] = original_domain


def _spin_for(node: Node, duration_sec: float) -> None:
    """Spin a node for a fixed duration to process callbacks."""
    deadline = time.time() + duration_sec
    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.05)


def _publish_robot_health(node: Node, publisher, robot_id: str, duration_sec: float, hz: float = 1.0) -> None:
    """Publish RobotHealth at a fixed rate for duration_sec."""
    period = 1.0 / hz
    deadline = time.time() + duration_sec
    msg = RobotHealth()
    msg.robot_name = robot_id
    msg.battery_percentage = 100.0
    msg.cpu_load = 0.1
    msg.memory_usage = 0.1
    msg.temperature = 30.0
    msg.is_connected = True

    while time.time() < deadline:
        msg.timestamp = node.get_clock().now().to_msg()
        publisher.publish(msg)
        rclpy.spin_once(node, timeout_sec=0.0)
        time.sleep(period)


def _wait_for_publishers(node: Node, topic: str, min_count: int = 1, timeout_sec: float = 5.0) -> bool:
    """Wait until topic has at least min_count publishers."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.05)
        if node.count_publishers(topic) >= min_count:
            return True
    return False


def _wait_for_degraded_status(node: Node, received, robot_id: str, timeout_sec: float = 8.0):
    """Wait for a DEGRADED system status that includes robot_id in error_message."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.05)
        for msg in received:
            if msg.status == 'DEGRADED' and robot_id in msg.error_message:
                return msg
    return None


def test_heartbeat_timeout_degrades(ros_node: Node):
    """Verify missing robot heartbeat degrades system health status."""
    publisher = ros_node.create_publisher(RobotHealth, '/robot1/robot_health', 10)
    received_messages = []

    subscription = ros_node.create_subscription(
        NodeStatus,
        '/coordination/system_health',
        lambda msg: received_messages.append(msg),
        10,
    )

    try:
        assert _wait_for_publishers(ros_node, '/coordination/system_health', timeout_sec=5.0), (
            'No publisher detected on /coordination/system_health'
        )
        _spin_for(ros_node, 0.5)
        _publish_robot_health(ros_node, publisher, 'robot1', duration_sec=2.0, hz=1.0)
        received_messages.clear()

        status = _wait_for_degraded_status(ros_node, received_messages, 'robot1', timeout_sec=8.0)
        assert status is not None, 'Expected DEGRADED system health after heartbeat timeout'
        assert status.status == 'DEGRADED'
        assert 'robot1' in status.error_message
    finally:
        ros_node.destroy_subscription(subscription)
