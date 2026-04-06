"""ROS 2 map merge status node."""

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from mapping.map_merger import map_merge_status


class MapMergeStatusNode(Node):
    def __init__(self):
        super().__init__('map_merge_status_node')
        self.minimum_required = int(self.declare_parameter('minimum_required', 2).value)
        self.create_subscription(String, 'mapping/maps_available', self._on_maps, 10)
        self.pub = self.create_publisher(String, 'mapping/map_merge_status', 10)

    def _on_maps(self, msg):
        try:
            payload = json.loads(msg.data)
            available_maps = payload['maps']
        except (KeyError, TypeError, json.JSONDecodeError):
            self.get_logger().warning('Invalid maps payload')
            return

        status = map_merge_status(available_maps, self.minimum_required)
        out = String()
        out.data = json.dumps(status)
        self.pub.publish(out)


def main():
    rclpy.init()
    node = MapMergeStatusNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
