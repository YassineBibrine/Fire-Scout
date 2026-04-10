from .frontier_logic import FrontierCandidate, select_frontiers


def main() -> None:
    import importlib
    from typing import List

    rclpy = importlib.import_module('rclpy')
    PoseStamped = importlib.import_module('geometry_msgs.msg').PoseStamped
    Node = importlib.import_module('rclpy.node').Node

    msg_module = importlib.import_module('firescout_interfaces.msg')
    Frontier = msg_module.Frontier
    FrontierArray = msg_module.FrontierArray

    class FrontierDetectorNode(Node):
        def __init__(self) -> None:
            super().__init__('frontier_detector')
            self.declare_parameter('robot_id', 'robot1')
            self.declare_parameter('frontier_min_size', 0.5)
            self.declare_parameter('frontier_max_travel_cost', 100.0)
            self.robot_id = str(self.get_parameter('robot_id').value)
            self.publisher = self.create_publisher(FrontierArray, '/coordination/frontiers', 10)
            self.timer = self.create_timer(1.0, self._publish_frontiers)

        def _sample_frontiers(self) -> List[FrontierCandidate]:
            return [
                FrontierCandidate(
                    frontier_id=f'{self.robot_id}_f1',
                    robot_id=self.robot_id,
                    area_m2=1.0,
                    info_gain=8.0,
                    travel_cost=4.0,
                    reachable=True,
                ),
                FrontierCandidate(
                    frontier_id=f'{self.robot_id}_f2',
                    robot_id=self.robot_id,
                    area_m2=0.2,
                    info_gain=10.0,
                    travel_cost=2.0,
                    reachable=True,
                ),
                FrontierCandidate(
                    frontier_id=f'{self.robot_id}_f3',
                    robot_id=self.robot_id,
                    area_m2=0.7,
                    info_gain=7.0,
                    travel_cost=3.0,
                    reachable=True,
                ),
            ]

        def _publish_frontiers(self) -> None:
            min_size = float(self.get_parameter('frontier_min_size').value)
            max_travel_cost = float(self.get_parameter('frontier_max_travel_cost').value)
            selected = select_frontiers(self._sample_frontiers(), min_size, max_travel_cost)

            msg = FrontierArray()
            msg.robot_id = self.robot_id

            now = self.get_clock().now().to_msg()
            msg.stamp = now

            frontiers = []
            for candidate in selected:
                frontier = Frontier()
                frontier.frontier_id = candidate.frontier_id
                frontier.robot_id = candidate.robot_id
                pose = PoseStamped()
                pose.header.stamp = now
                pose.header.frame_id = 'map'
                pose.pose.orientation.w = 1.0
                frontier.centroid = pose
                frontier.area_m2 = float(candidate.area_m2)
                frontier.info_gain = float(candidate.info_gain)
                frontier.travel_cost = float(candidate.travel_cost)
                frontier.reachable = bool(candidate.reachable)
                frontiers.append(frontier)

            msg.frontiers = frontiers
            self.publisher.publish(msg)

    rclpy.init()
    node = FrontierDetectorNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
