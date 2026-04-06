"""ROS 2 dummy Odometry publisher."""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry


class OdomPubNode(Node):
    def __init__(self):
        super().__init__('dummy_odom_pub')
        self.pub = self.create_publisher(Odometry, 'odom', 10)
        self.create_timer(0.5, self._tick)

    def _tick(self):
        msg = Odometry()
        msg.pose.pose.position.x = 0.0
        msg.pose.pose.position.y = 0.0
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = OdomPubNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
