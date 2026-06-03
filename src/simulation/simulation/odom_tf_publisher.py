#!/usr/bin/python3
"""Publish odom -> base_link TF from odometry messages."""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster


class OdomTfPublisher(Node):
    def __init__(self):
        super().__init__('odom_tf_publisher')
        self._tf_broadcaster = TransformBroadcaster(self)
        self._sub = self.create_subscription(
            Odometry, '~/odom', self._odom_callback, 10)

    def _odom_callback(self, msg: Odometry):
        t = TransformStamped()
        t.header.stamp = msg.header.stamp
        ns = self.get_namespace().strip('/')
        prefix = f'{ns}/' if ns else ''
        t.header.frame_id = prefix + msg.header.frame_id
        t.child_frame_id = prefix + msg.child_frame_id
        t.transform.translation.x = msg.pose.pose.position.x
        t.transform.translation.y = msg.pose.pose.position.y
        t.transform.translation.z = msg.pose.pose.position.z
        t.transform.rotation = msg.pose.pose.orientation
        self._tf_broadcaster.sendTransform(t)


def main():
    rclpy.init()
    node = OdomTfPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
