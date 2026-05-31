import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


class DummyCameraPub(Node):

    def __init__(self):

        super().__init__('dummy_camera_pub')

        self.declare_parameter(
            'robot_id',
            'robot1'
        )
        self.declare_parameter(
            'use_sim_time',
            True
        )

        self.robot_id = self.get_parameter(
            'robot_id'
        ).value

        self.publisher_ = self.create_publisher(
            Image,
            f'/{self.robot_id}/camera/image_raw',
            10
        )

        self.timer = self.create_timer(
            0.2,
            self.publish_image
        )

    def publish_image(self):

        msg = Image()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = f'{self.robot_id}/camera_frame'
        msg.height = 480
        msg.width = 640
        msg.encoding = 'rgb8'
        msg.is_bigendian = False
        msg.step = msg.width * 3
        msg.data = bytes([128] * msg.width * msg.height * 3)

        self.publisher_.publish(msg)


def main(args=None):

    rclpy.init(args=args)

    node = DummyCameraPub()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
