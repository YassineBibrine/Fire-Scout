from importlib import import_module

import rclpy
from rclpy.node import Node

# Resolve generated message dynamically to avoid IDE false positives.
RobotHealth = getattr(import_module('firescout_interfaces.msg'), 'RobotHealth')


class DummyHeartbeatPub(Node):

    def __init__(self):

        super().__init__('dummy_heartbeat_pub')

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
            RobotHealth,
            f'/{self.robot_id}/robot_health',
            10
        )

        self.timer = self.create_timer(
            1.0,
            self.publish_health
        )

    def publish_health(self):

        msg = RobotHealth()
        msg.robot_name = self.robot_id
        msg.battery_percentage = 85.0
        msg.cpu_load = 20.0
        msg.memory_usage = 30.0
        msg.temperature = 45.0
        msg.is_connected = True
        msg.timestamp = self.get_clock().now().to_msg()

        self.publisher_.publish(msg)


def main(args=None):

    rclpy.init(args=args)

    node = DummyHeartbeatPub()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
