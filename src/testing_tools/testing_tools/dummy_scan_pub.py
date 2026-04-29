import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class DummyScanPub(Node):

    def __init__(self):

        super().__init__('dummy_scan_pub')

        self.declare_parameter(
            'robot_id',
            'robot1'
        )
        self.declare_parameter(
            'scan_rate_hz',
            10.0
        )
        self.declare_parameter(
            'use_sim_time',
            True
        )

        self.robot_id = self.get_parameter(
            'robot_id'
        ).value
        scan_rate_hz = float(self.get_parameter(
            'scan_rate_hz'
        ).value)

        self.publisher_ = self.create_publisher(
            LaserScan,
            f'/{self.robot_id}/scan',
            10
        )

        period = 1.0 / scan_rate_hz if scan_rate_hz > 0.0 else 0.1
        self.timer = self.create_timer(
            period,
            self.publish_scan
        )

    def publish_scan(self):

        msg = LaserScan()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = f'{self.robot_id}/base_scan'
        msg.angle_min = -3.14
        msg.angle_max = 3.14
        msg.angle_increment = 0.0175
        msg.range_min = 0.12
        msg.range_max = 12.0
        msg.ranges = [3.0] * 360

        self.publisher_.publish(msg)


def main(args=None):

    rclpy.init(args=args)

    node = DummyScanPub()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
