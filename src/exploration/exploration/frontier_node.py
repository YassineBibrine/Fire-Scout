"""ROS 2 frontier node that extracts frontiers from occupancy grids."""

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from exploration.frontier_detector import extract_frontiers


class FrontierNode(Node):
    def __init__(self):
        super().__init__('frontier_node')
        self.create_subscription(String, 'exploration/occupancy_grid', self._on_grid, 10)
        self.frontier_pub = self.create_publisher(String, 'exploration/frontiers', 10)

    def _on_grid(self, msg):
        try:
            payload = json.loads(msg.data)
            grid = payload['grid']
        except (KeyError, TypeError, json.JSONDecodeError):
            self.get_logger().warning('Invalid grid payload')
            return

        out = String()
        out.data = json.dumps({'frontiers': extract_frontiers(grid)})
        self.frontier_pub.publish(out)


def main():
    rclpy.init()
    node = FrontierNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
