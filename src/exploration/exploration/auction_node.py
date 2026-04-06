"""ROS 2 auction node for selecting exploration task winners."""

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from exploration.auction_orchestrator import resolve_with_timeout


class AuctionNode(Node):
    def __init__(self):
        super().__init__('auction_node')
        self.default_timeout_s = float(self.declare_parameter('timeout_s', 1.0).value)
        self.create_subscription(String, 'exploration/auction_bids', self._on_bids, 10)
        self.winner_pub = self.create_publisher(String, 'exploration/auction_result', 10)

    def _on_bids(self, msg):
        try:
            payload = json.loads(msg.data)
            task_id = payload['task_id']
            bids = payload['bids']
            opened_at_s = float(payload.get('opened_at_s', 0.0))
            now_s = float(payload.get('now_s', opened_at_s + self.default_timeout_s))
            timeout_s = float(payload.get('timeout_s', self.default_timeout_s))
        except (KeyError, ValueError, TypeError, json.JSONDecodeError):
            self.get_logger().warning('Invalid auction payload')
            return

        winner = resolve_with_timeout(bids, opened_at_s, now_s, timeout_s)
        if winner is None:
            return

        out = String()
        out.data = json.dumps({'task_id': task_id, 'winner': winner})
        self.winner_pub.publish(out)


def main():
    rclpy.init()
    node = AuctionNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
