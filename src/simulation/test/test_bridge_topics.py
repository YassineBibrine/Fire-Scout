import time
import importlib.util
from pathlib import Path

import pytest
pytest.importorskip('rclpy')
pytest.importorskip('sensor_msgs.msg')
pytest.importorskip('nav_msgs.msg')
import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


@pytest.fixture(scope='module')
def ros_node():
    rclpy.init()
    node = Node('test_bridge_topics_node')
    try:
        yield node
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


def _wait_for_topic_type(node, topic_name, expected_type, timeout_sec=4.0):
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
        for name, types in node.get_topic_names_and_types():
            if name == topic_name and expected_type in types:
                return True
    return False


def test_bridge_topics(ros_node):
    scan_pub = ros_node.create_publisher(LaserScan, '/robot1/scan', 10)
    odom_pub = ros_node.create_publisher(Odometry, '/robot1/odom', 10)
    scan_pub.publish(LaserScan())
    odom_pub.publish(Odometry())
    assert _wait_for_topic_type(ros_node, '/robot1/scan', 'sensor_msgs/msg/LaserScan')
    assert _wait_for_topic_type(ros_node, '/robot1/odom', 'nav_msgs/msg/Odometry')


def _load_launch_module(path: Path):
    module_name = f"_launch_{path.name.replace('.', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_robot_bridge_uses_robot_specific_lidar_topic():
    launch_path = Path(__file__).resolve().parents[1] / 'launch' / 'bridge_robot.launch.py'
    module = _load_launch_module(launch_path)
    source = launch_path.read_text(encoding='utf-8')

    assert module.generate_launch_description().entities
    assert "'bridge_names': ['cmd_vel', 'odometry', 'lidar', 'camera']" in source
    assert 'lidar_world' not in source
    assert "PathJoinSubstitution(['/', robot_id, 'scan'])" in source
    assert 'bridges.lidar.gz_topic_name' in source
