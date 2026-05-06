from importlib import import_module
import os
import subprocess
import sys
import time

import pytest
pytest.importorskip('rclpy')
pytest.importorskip('firescout_interfaces.msg')
import rclpy
MissionState = getattr(import_module('firescout_interfaces.msg'), 'MissionState')
NodeStatus = getattr(import_module('firescout_interfaces.msg'), 'NodeStatus')
from rclpy.node import Node


@pytest.fixture(scope='function')
def ros_node():
    """Start fault supervisor node and provide a helper ROS node."""
    original_domain = os.environ.get('ROS_DOMAIN_ID')
    os.environ['ROS_DOMAIN_ID'] = '82'
    process = None
    node = None
    try:
        rclpy.init()
        node = Node('test_fault_reassignment_node')
        env = os.environ.copy()
        process = subprocess.Popen(
            [
                sys.executable,
                '-m',
                'coordination.fault_supervisor_node',
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
            raise RuntimeError(f'fault_supervisor_node exited early:\n{output}')
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


def _wait_for_mission_state(node: Node, received, timeout_sec: float = 4.0):
    """Wait for a MissionState message to arrive."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.05)
        for msg in received:
            if msg.state == 'DEGRADED':
                return msg
    return None


def _publish_system_health(node: Node, publisher, robot_id: str, duration_sec: float, hz: float = 2.0) -> None:
    """Publish degraded system health for duration_sec to ensure reception."""
    period = 1.0 / hz
    deadline = time.time() + duration_sec
    msg = NodeStatus()
    msg.node_name = 'system_health'
    msg.status = 'DEGRADED'
    msg.error_message = robot_id
    msg.uptime_seconds = 0.0

    while time.time() < deadline:
        msg.last_heartbeat = node.get_clock().now().to_msg()
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


def _wait_for_subscribers(publisher, min_count: int = 1, timeout_sec: float = 5.0) -> bool:
    """Wait until publisher reports at least min_count subscribers."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if publisher.get_subscription_count() >= min_count:
            return True
        time.sleep(0.05)
    return False


def test_fault_reassignment_removes_robot(ros_node: Node):
    """Verify degraded system health removes the degraded robot from mission state."""
    publisher = ros_node.create_publisher(NodeStatus, '/coordination/system_health', 10)
    received_messages = []

    subscription = ros_node.create_subscription(
        MissionState,
        '/mission/state',
        lambda msg: received_messages.append(msg),
        10,
    )

    try:
        assert _wait_for_subscribers(publisher, timeout_sec=5.0), (
            'No subscribers detected on /coordination/system_health'
        )
        assert _wait_for_publishers(ros_node, '/mission/state', timeout_sec=5.0), (
            'No publisher detected on /mission/state'
        )
        _spin_for(ros_node, 0.5)

        _publish_system_health(ros_node, publisher, 'robot2', duration_sec=3.0, hz=2.0)

        mission_state = _wait_for_mission_state(ros_node, received_messages, timeout_sec=6.0)
        assert mission_state is not None, 'No MissionState received after degraded system health'
        assert mission_state.state == 'DEGRADED'
        assert 'robot2' not in mission_state.active_robots
    finally:
        ros_node.destroy_subscription(subscription)
