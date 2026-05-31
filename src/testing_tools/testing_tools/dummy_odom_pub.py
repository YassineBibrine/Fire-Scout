import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry


class DummyOdomPub(Node):

    def __init__(self):

        super().__init__('dummy_odom_pub')

        self.declare_parameter(
            'robot_id',
            'robot1'
        )
        self.declare_parameter(
            'odom_rate_hz',
            20.0
        )
        self.declare_parameter(
            'use_sim_time',
            True
        )

        self.robot_id = self.get_parameter(
            'robot_id'
        ).value
        odom_rate_hz = float(self.get_parameter(
            'odom_rate_hz'
        ).value)

        self.publisher_ = self.create_publisher(
            Odometry,
            f'/{self.robot_id}/odom',
            10
        )

        period = 1.0 / odom_rate_hz if odom_rate_hz > 0.0 else 0.05
        self.timer = self.create_timer(
            period,
            self.publish_odom
        )

    def publish_odom(self):

        msg = Odometry()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = f'{self.robot_id}/odom'
        msg.child_frame_id = f'{self.robot_id}/base_footprint'

        self.publisher_.publish(msg)


def main(args=None):

    rclpy.init(args=args)

    node = DummyOdomPub()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
