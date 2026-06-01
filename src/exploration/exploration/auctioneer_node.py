from collections import defaultdict
from typing import DefaultDict, List

from .auction_logic import AuctionBid as LogicalBid
from .auction_logic import select_winner


def main() -> None:
    import importlib

    rclpy = importlib.import_module('rclpy')
    PoseStamped = importlib.import_module('geometry_msgs.msg').PoseStamped
    Node = importlib.import_module('rclpy.node').Node

    msg_module = importlib.import_module('firescout_interfaces.msg')
    AuctionBid = msg_module.AuctionBid
    AuctionResult = msg_module.AuctionResult

    class AuctioneerNode(Node):
        def __init__(self) -> None:
            super().__init__('auctioneer')
            self.declare_parameter('auction_timeout_sec', 1.0)
            self.declare_parameter('bid_collection_sec', 0.3)
            self.declare_parameter('task_type', 1)
            self.bid_cache: DefaultDict[str, List[LogicalBid]] = defaultdict(list)
            self.first_bid_time = {}
            self.subscription = self.create_subscription(
                AuctionBid,
                '/coordination/auction_bids',
                self._on_bid,
                10,
            )
            self.publisher = self.create_publisher(AuctionResult, '/coordination/auction_result', 10)
            self.timer = self.create_timer(0.5, self._publish_results)

        def _on_bid(self, msg) -> None:
            self.first_bid_time.setdefault(
                msg.auction_id,
                self.get_clock().now().nanoseconds / 1e9,
            )
            self.bid_cache[msg.auction_id].append(
                LogicalBid(
                    auction_id=msg.auction_id,
                    robot_id=msg.robot_id,
                    candidate_frontier_id=msg.candidate_frontier_id,
                    utility_score=float(msg.utility_score),
                    eta_sec=float(msg.eta_sec),
                    energy_cost=float(msg.energy_cost),
                        target_pose=msg.target_pose,
                )
            )

        def _publish_results(self) -> None:
            timeout_sec = float(self.get_parameter('auction_timeout_sec').value)
            collection_sec = float(self.get_parameter('bid_collection_sec').value)
            now_sec = self.get_clock().now().nanoseconds / 1e9
            for auction_id in list(self.bid_cache.keys()):
                if now_sec - self.first_bid_time[auction_id] < collection_sec:
                    continue
                selection = select_winner(self.bid_cache[auction_id], timeout_sec)
                if selection is None:
                    del self.bid_cache[auction_id]
                    del self.first_bid_time[auction_id]
                    continue

                result = AuctionResult()
                result.auction_id = auction_id
                result.winner_robot_id = selection.winner.robot_id
                result.task_id = selection.winner.candidate_frontier_id
                result.task_type = int(self.get_parameter('task_type').value)

                if selection.winner.target_pose is not None:
                    result.target_pose = selection.winner.target_pose
                else:
                    pose = PoseStamped()
                    pose.header.stamp = self.get_clock().now().to_msg()
                    pose.header.frame_id = 'map'
                    pose.pose.orientation.w = 1.0
                    result.target_pose = pose

                self.publisher.publish(result)
                del self.bid_cache[auction_id]
                del self.first_bid_time[auction_id]

    rclpy.init()
    node = AuctioneerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
