from .bidder_logic import score_frontier


def main() -> None:
    import importlib

    rclpy = importlib.import_module('rclpy')
    Node = importlib.import_module('rclpy.node').Node

    msg_module = importlib.import_module('firescout_interfaces.msg')
    AuctionBid = msg_module.AuctionBid
    FrontierArray = msg_module.FrontierArray

    class BidderNode(Node):
        def __init__(self) -> None:
            super().__init__('bidder')
            self.declare_parameter('robot_id', 'robot1')
            self.declare_parameter('speed_mps', 0.7)
            self.declare_parameter('energy_rate', 0.5)
            self.robot_id = str(self.get_parameter('robot_id').value)

            self.subscription = self.create_subscription(
                FrontierArray,
                '/coordination/frontiers',
                self._on_frontiers,
                10,
            )
            self.publisher = self.create_publisher(AuctionBid, '/coordination/auction_bids', 10)

        def _on_frontiers(self, msg) -> None:
            if not msg.frontiers:
                return

            now = self.get_clock().now().to_msg()
            bid_count = 0
            for frontier in msg.frontiers:
                if frontier.robot_id and frontier.robot_id != self.robot_id:
                    continue

                score = score_frontier(
                    info_gain=float(frontier.info_gain),
                    travel_cost=float(frontier.travel_cost),
                    speed_mps=float(self.get_parameter('speed_mps').value),
                    energy_rate=float(self.get_parameter('energy_rate').value),
                )

                bid = AuctionBid()
                bid.auction_id = f'auction:{frontier.frontier_id}'
                bid.robot_id = self.robot_id
                bid.candidate_frontier_id = frontier.frontier_id
                bid.utility_score = float(score.utility_score)
                bid.eta_sec = float(score.eta_sec)
                bid.energy_cost = float(score.energy_cost)
                bid.target_pose = frontier.centroid
                bid.timestamp = now
                self.publisher.publish(bid)
                bid_count += 1

            if bid_count > 0:
                self.get_logger().info(
                    f'Bidder: received {len(msg.frontiers)} frontiers from {msg.robot_id}, '
                    f'placed {bid_count} bids'
                )

    rclpy.init()
    node = BidderNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
