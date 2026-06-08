from importlib import import_module
from typing import Any
import os
import subprocess
import sys
import time

import pytest
pytest.importorskip('rclpy')
pytest.importorskip('firescout_interfaces.msg')
pytest.importorskip('geometry_msgs.msg')
import rclpy
AuctionResult = getattr(import_module('firescout_interfaces.msg'), 'AuctionResult')
TaskAssignment = getattr(import_module('firescout_interfaces.msg'), 'TaskAssignment')
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node


@pytest.fixture(scope='function')
def ros_node():
    """Start task allocator node and provide a helper ROS node."""
    original_domain = os.environ.get('ROS_DOMAIN_ID')
    os.environ['ROS_DOMAIN_ID'] = '83'
    process = None
    node = None
    try:
        rclpy.init()
        node = Node('test_task_allocation_node')
        env = os.environ.copy()
        process = subprocess.Popen(
            [
                sys.executable,
                '-m',
                'coordination.task_allocator_node',
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
            raise RuntimeError(f'task_allocator_node exited early:\n{output}')
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


def _wait_for_assignment(node: Node, received, task_id: str, assigned_robot: str, timeout_sec: float = 4.0):
    """Wait for a TaskAssignment with matching task_id and assigned_robot."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.05)
        for msg in received:
            if msg.task_id == task_id and msg.assigned_robot == assigned_robot:
                return msg
    return None


def _publish_auction_result(node: Node, publisher, auction: Any, duration_sec: float, hz: float = 2.0) -> None:
    """Publish AuctionResult for duration_sec to ensure reception."""
    period = 1.0 / hz
    deadline = time.time() + duration_sec

    while time.time() < deadline:
        auction.timestamp = node.get_clock().now().to_msg()
        publisher.publish(auction)
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


def _wait_for_subscribers(publisher, node: Node, min_count: int = 1, timeout_sec: float = 10.0) -> bool:
    """Wait until publisher reports at least min_count subscribers."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.05)
        if publisher.get_subscription_count() >= min_count:
            return True
    return False


def test_task_allocation_publishes_assignment(ros_node: Node):
    """Verify AuctionResult produces a TaskAssignment for the winning robot."""
    publisher = ros_node.create_publisher(AuctionResult, '/coordination/auction_result', 10)
    received_messages = []

    subscription = ros_node.create_subscription(
        TaskAssignment,
        '/coordination/task_assignments',
        lambda msg: received_messages.append(msg),
        10,
    )

    try:
        assert _wait_for_subscribers(publisher, ros_node, timeout_sec=10.0), (
            'No subscribers detected on /coordination/auction_result'
        )
        assert _wait_for_publishers(ros_node, '/coordination/task_assignments', timeout_sec=5.0), (
            'No publisher detected on /coordination/task_assignments'
        )
        _spin_for(ros_node, 0.5)

        auction = AuctionResult()
        auction.auction_id = 'a1'
        auction.winner_robot_id = 'robot1'
        auction.task_id = 'frontier_1'
        auction.task_type = 1

        target = PoseStamped()
        target.header.frame_id = 'map'
        target.header.stamp = ros_node.get_clock().now().to_msg()
        target.pose.position.x = 0.0
        target.pose.position.y = 0.0
        target.pose.position.z = 0.0
        target.pose.orientation.x = 0.0
        target.pose.orientation.y = 0.0
        target.pose.orientation.z = 0.0
        target.pose.orientation.w = 1.0

        auction.target_pose = target
        auction.timestamp = ros_node.get_clock().now().to_msg()

        _publish_auction_result(ros_node, publisher, auction, duration_sec=3.0, hz=2.0)

        assignment = _wait_for_assignment(ros_node, received_messages, 'frontier_1', 'robot1', timeout_sec=6.0)
        assert assignment is not None, 'No TaskAssignment received after AuctionResult'
        assert assignment.task_id == 'frontier_1'
        assert assignment.assigned_robot == 'robot1'
    finally:
        ros_node.destroy_subscription(subscription)
