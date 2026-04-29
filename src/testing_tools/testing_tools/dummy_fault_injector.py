from importlib import import_module

import rclpy
from rclpy.node import Node

# Resolve generated message dynamically to avoid IDE false positives.
FaultEvent = getattr(import_module('firescout_interfaces.msg'), 'FaultEvent')


class DummyFaultInjector(Node):

    def __init__(self):

        super().__init__('dummy_fault_injector')

        self.declare_parameter(
            'robot_id',
            'robot2'
        )
        self.declare_parameter(
            'use_sim_time',
            True
        )

        self.robot_id = self.get_parameter(
            'robot_id'
        ).value

        self.publisher_ = self.create_publisher(
            FaultEvent,
            '/coordination/fault_events',
            10
        )

        self.timer = self.create_timer(
            3.0,
            self.publish_once
        )
        self.published = False

    def publish_once(self):

        if self.published:
            return

        msg = FaultEvent()
        msg.robot_id = self.robot_id
        msg.fault_type = 'lidar_timeout'
        msg.severity = 'WARNING'
        msg.description = 'Simulated fault injection'
        msg.timestamp = self.get_clock().now().to_msg()

        self.publisher_.publish(msg)
        self.published = True


def main(args=None):

    rclpy.init(args=args)

    node = DummyFaultInjector()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
