import math

from .frontier_logic import FrontierCandidate, select_frontiers


def main() -> None:
    import importlib
    from typing import List

    rclpy = importlib.import_module('rclpy')
    PoseStamped = importlib.import_module('geometry_msgs.msg').PoseStamped
    OccupancyGrid = importlib.import_module('nav_msgs.msg').OccupancyGrid
    Odometry = importlib.import_module('nav_msgs.msg').Odometry
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
            self._latest_map = None
            self._odom_seen = False
            self.create_subscription(OccupancyGrid, f'/{self.robot_id}/map', self._on_map, 10)
            self.create_subscription(Odometry, f'/{self.robot_id}/odom', self._on_odom, 10)
            self.publisher = self.create_publisher(FrontierArray, '/coordination/frontiers', 10)
            self.timer = self.create_timer(1.0, self._publish_frontiers)

        def _on_map(self, msg) -> None:
            self._latest_map = msg

        def _on_odom(self, _msg) -> None:
            self._odom_seen = True

        def _extract_frontiers(self) -> List[FrontierCandidate]:
            if self._latest_map is None:
                if not self._odom_seen:
                    return []
                # Publish exploration targets to bootstrap mapping
                # These targets encourage robots to explore and build maps
                import random
                random.seed(self.robot_id)
                return [
                    FrontierCandidate(
                        frontier_id=f'{self.robot_id}_explore_{i}',
                        robot_id=self.robot_id,
                        area_m2=1.0,
                        info_gain=10.0,
                        travel_cost=5.0 * (i + 1),
                        reachable=True,
                        centroid_x=random.uniform(-5.0, 5.0),
                        centroid_y=random.uniform(-5.0, 5.0),
                    )
                    for i in range(3)
                ]

            grid = self._latest_map
            width = int(grid.info.width)
            height = int(grid.info.height)
            resolution = float(grid.info.resolution)
            origin_x = float(grid.info.origin.position.x)
            origin_y = float(grid.info.origin.position.y)
            data = list(grid.data)

            def cell_index(x: int, y: int) -> int:
                return y * width + x

            def is_frontier_cell(x: int, y: int) -> bool:
                if x <= 0 or y <= 0 or x >= width - 1 or y >= height - 1:
                    return False
                if data[cell_index(x, y)] != 0:
                    return False
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if data[cell_index(nx, ny)] < 0:
                        return True
                return False

            visited = set()
            candidates: List[FrontierCandidate] = []
            for y in range(1, height - 1):
                for x in range(1, width - 1):
                    if (x, y) in visited or not is_frontier_cell(x, y):
                        continue

                    queue = [(x, y)]
                    cluster = []
                    visited.add((x, y))

                    while queue:
                        cx, cy = queue.pop()
                        cluster.append((cx, cy))
                        for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                            if (nx, ny) in visited:
                                continue
                            if 1 <= nx < width - 1 and 1 <= ny < height - 1 and is_frontier_cell(nx, ny):
                                visited.add((nx, ny))
                                queue.append((nx, ny))

                    if not cluster:
                        continue

                    centroid_x = sum((cx + 0.5) * resolution for cx, _ in cluster) / len(cluster) + origin_x
                    centroid_y = sum((cy + 0.5) * resolution for _, cy in cluster) / len(cluster) + origin_y
                    area_m2 = len(cluster) * resolution * resolution
                    travel_cost = math.hypot(centroid_x, centroid_y)
                    info_gain = float(len(cluster))
                    candidates.append(
                        FrontierCandidate(
                            frontier_id=f'{self.robot_id}_f{len(candidates) + 1}',
                            robot_id=self.robot_id,
                            area_m2=area_m2,
                            info_gain=info_gain,
                            travel_cost=travel_cost,
                            reachable=True,
                            centroid_x=centroid_x,
                            centroid_y=centroid_y,
                        )
                    )

            return candidates

        def _publish_frontiers(self) -> None:
            min_size = float(self.get_parameter('frontier_min_size').value)
            max_travel_cost = float(self.get_parameter('frontier_max_travel_cost').value)
            selected = select_frontiers(self._extract_frontiers(), min_size, max_travel_cost)

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
                pose.pose.position.x = float(candidate.centroid_x)
                pose.pose.position.y = float(candidate.centroid_y)
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
