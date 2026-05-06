import subprocess
import time

import pytest
pytest.importorskip('geometry_msgs.msg')
pytest.importorskip('nav_msgs.msg')
pytest.importorskip('rclpy')
pytest.importorskip('tf2_msgs.msg')

import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node
from tf2_msgs.msg import TFMessage


def test_slam_wrapper_publishes_corrected_odom_tf():
    rclpy.init()
    node = Node('test_slam_wrapper_tf_node')
    process = subprocess.Popen([
        'ros2',
        'run',
        'mapping',
        'slam_wrapper_node',
        '--ros-args',
        '-p',
        'robot_id:=robot1',
    ])

    odom_pub = node.create_publisher(Odometry, '/robot1/odom', 10)
    received_tf = []

    def _on_tf(msg: TFMessage) -> None:
        received_tf.extend(msg.transforms)

    tf_sub = node.create_subscription(TFMessage, '/tf', _on_tf, 100)

    try:
        deadline = time.time() + 8.0
        while time.time() < deadline:
            odom = Odometry()
            odom.header.stamp = node.get_clock().now().to_msg()
            odom.header.frame_id = 'odom'
            odom.child_frame_id = 'base_link'
            odom.pose.pose.orientation.w = 1.0
            odom_pub.publish(odom)
            rclpy.spin_once(node, timeout_sec=0.1)

            if any(
                transform.header.frame_id == 'robot1/odom'
                and transform.child_frame_id == 'robot1/base_link'
                for transform in received_tf
            ):
                return

        assert False, 'slam_wrapper_node did not publish robot1/odom -> robot1/base_link TF'
    finally:
        node.destroy_subscription(tf_sub)
        node.destroy_node()
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        rclpy.shutdown()
