from importlib import import_module

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped

# Resolve generated message classes dynamically to avoid IDE false positives.
Frontier = getattr(import_module('firescout_interfaces.msg'), 'Frontier')
FrontierArray = getattr(import_module('firescout_interfaces.msg'), 'FrontierArray')


class DummyFrontierPub(Node):

    def __init__(self):

        super().__init__('dummy_frontier_pub')

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
            FrontierArray,
            '/coordination/frontiers',
            10
        )

        self.timer = self.create_timer(
            1.0,
            self.publish_frontiers
        )

    def _build_frontier(self, frontier_id, area_m2, info_gain, travel_cost, x, y):

        centroid = PoseStamped()
        centroid.header.frame_id = 'map'
        centroid.pose.position.x = float(x)
        centroid.pose.position.y = float(y)

        frontier = Frontier()
        frontier.frontier_id = frontier_id
        frontier.robot_id = self.robot_id
        frontier.centroid = centroid
        frontier.area_m2 = float(area_m2)
        frontier.info_gain = float(info_gain)
        frontier.travel_cost = float(travel_cost)
        frontier.reachable = True

        return frontier

    def publish_frontiers(self):

        f1 = self._build_frontier(
            f'{self.robot_id}_f1',
            1.5,
            8.0,
            3.0,
            2.0,
            1.0
        )
        f2 = self._build_frontier(
            f'{self.robot_id}_f2',
            0.8,
            6.0,
            5.0,
            -1.0,
            3.0
        )

        msg = FrontierArray()
        msg.robot_id = self.robot_id
        msg.timestamp = self.get_clock().now().to_msg()
        msg.frontiers = [f1, f2]

        self.publisher_.publish(msg)


def main(args=None):

    rclpy.init(args=args)

    node = DummyFrontierPub()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
