"""ROS 2 dummy LaserScan publisher."""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class ScanPubNode(Node):
    def __init__(self):
        super().__init__('dummy_scan_pub')
        self.pub = self.create_publisher(LaserScan, 'scan', 10)
        self.create_timer(0.5, self._tick)

    def _tick(self):
        msg = LaserScan()
        msg.angle_min = -1.57
        msg.angle_max = 1.57
        msg.range_min = 0.1
        msg.range_max = 10.0
        msg.ranges = [1.0, 1.2, 1.1]
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = ScanPubNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
