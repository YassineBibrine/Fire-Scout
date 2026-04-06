"""ROS 2 dummy Image publisher."""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


class CameraPubNode(Node):
    def __init__(self):
        super().__init__('dummy_camera_pub')
        self.pub = self.create_publisher(Image, 'camera/image_raw', 10)
        self.create_timer(1.0, self._tick)

    def _tick(self):
        msg = Image()
        msg.height = 2
        msg.width = 2
        msg.encoding = 'rgb8'
        msg.step = 6
        msg.data = bytes([0, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 255])
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = CameraPubNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
