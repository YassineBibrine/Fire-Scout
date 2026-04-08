#!/usr/bin/env python3

"""Simple multi-robot occupancy grid merge node.

This node subscribes to robot-local map topics and publishes a merged global map.
Merge strategy:
- Build a common global grid that covers all currently available robot maps.
- Project each known cell into that grid using map origin + resolution metadata.
- Overlay known values into the merged grid (occupied cells dominate free cells).

Unknown cells remain -1 when no map contributes data for those locations.
"""

import math
from typing import Dict, List, Optional, Tuple

import rclpy
from nav_msgs.msg import OccupancyGrid
from rclpy.node import Node
from std_msgs.msg import String


class MapMergeNode(Node):
    """Merges occupancy grids from robot1/2/3 into a single global map."""

    def __init__(self) -> None:
        super().__init__("map_merge_node")

        # Parameters controlling output map characteristics and publish cadence.
        self.declare_parameter("map_resolution", 0.05)
        self.declare_parameter("merge_rate_hz", 1.0)

        self._map_resolution = float(self.get_parameter("map_resolution").value)
        self._merge_rate_hz = float(self.get_parameter("merge_rate_hz").value)

        if self._map_resolution <= 0.0:
            self.get_logger().warn("map_resolution must be > 0.0. Falling back to 0.05")
            self._map_resolution = 0.05
        if self._merge_rate_hz <= 0.0:
            self.get_logger().warn("merge_rate_hz must be > 0.0. Falling back to 1.0")
            self._merge_rate_hz = 1.0

        # Keep latest map per robot. Missing maps remain None until received.
        self._latest_maps: Dict[str, Optional[OccupancyGrid]] = {
            "robot1": None,
            "robot2": None,
            "robot3": None,
        }

        # Subscribe to per-robot maps.
        self.create_subscription(OccupancyGrid, "/robot1/map", self._make_map_callback("robot1"), 10)
        self.create_subscription(OccupancyGrid, "/robot2/map", self._make_map_callback("robot2"), 10)
        self.create_subscription(OccupancyGrid, "/robot3/map", self._make_map_callback("robot3"), 10)

        # Global merged outputs.
        self._merged_map_pub = self.create_publisher(OccupancyGrid, "/map", 10)
        self._status_pub = self.create_publisher(String, "/mapping/map_merge_status", 10)

        # Publish merge output and status at configured rate.
        self.create_timer(1.0 / self._merge_rate_hz, self._publish_timer_callback)

        self.get_logger().info(
            f"MapMergeNode started: resolution={self._map_resolution}, "
            f"merge_rate_hz={self._merge_rate_hz}"
        )

    def _make_map_callback(self, robot_id: str):
        """Factory producing callbacks that store each robot's latest map."""

        def _callback(msg: OccupancyGrid) -> None:
            self._latest_maps[robot_id] = msg

        return _callback

    def _publish_timer_callback(self) -> None:
        """Compute status, merge available maps, and publish outputs."""
        available_maps = [m for m in self._latest_maps.values() if m is not None]
        num_available = len(available_maps)

        # Status follows strict required values.
        if num_available == 0:
            status = "NO_MAPS"
        elif num_available == len(self._latest_maps):
            status = "ALL_READY"
        else:
            status = f"PARTIAL_{num_available}"

        status_msg = String()
        status_msg.data = status
        self._status_pub.publish(status_msg)

        # No map data yet: publish only status and return gracefully.
        if num_available == 0:
            return

        merged = self._merge_maps(available_maps)
        if merged is not None:
            self._merged_map_pub.publish(merged)

    def _merge_maps(self, maps: List[OccupancyGrid]) -> Optional[OccupancyGrid]:
        """Create a merged OccupancyGrid from currently available maps."""
        if not maps:
            return None

        resolution = self._map_resolution

        # Determine global bounds from each map's origin, size, and resolution.
        min_x = math.inf
        min_y = math.inf
        max_x = -math.inf
        max_y = -math.inf

        for m in maps:
            origin_x = float(m.info.origin.position.x)
            origin_y = float(m.info.origin.position.y)
            map_res = float(m.info.resolution)
            width_m = float(m.info.width) * map_res
            height_m = float(m.info.height) * map_res

            min_x = min(min_x, origin_x)
            min_y = min(min_y, origin_y)
            max_x = max(max_x, origin_x + width_m)
            max_y = max(max_y, origin_y + height_m)

        if not all(math.isfinite(v) for v in [min_x, min_y, max_x, max_y]):
            return None

        # Compute output grid dimensions, ensuring at least one cell each axis.
        out_width = max(1, int(math.ceil((max_x - min_x) / resolution)))
        out_height = max(1, int(math.ceil((max_y - min_y) / resolution)))

        # Initialize merged grid with unknown values.
        merged_data = [-1] * (out_width * out_height)

        # Overlay each available map into merged grid.
        for m in maps:
            self._overlay_map(
                source_map=m,
                merged_data=merged_data,
                merged_width=out_width,
                merged_height=out_height,
                merged_min_x=min_x,
                merged_min_y=min_y,
                merged_resolution=resolution,
            )

        # Build outgoing OccupancyGrid message.
        merged_msg = OccupancyGrid()
        merged_msg.header.stamp = self.get_clock().now().to_msg()
        merged_msg.header.frame_id = "map"

        merged_msg.info.map_load_time = merged_msg.header.stamp
        merged_msg.info.resolution = resolution
        merged_msg.info.width = out_width
        merged_msg.info.height = out_height
        merged_msg.info.origin.position.x = min_x
        merged_msg.info.origin.position.y = min_y
        merged_msg.info.origin.position.z = 0.0
        merged_msg.info.origin.orientation.x = 0.0
        merged_msg.info.origin.orientation.y = 0.0
        merged_msg.info.origin.orientation.z = 0.0
        merged_msg.info.origin.orientation.w = 1.0

        merged_msg.data = merged_data
        return merged_msg

    def _overlay_map(
        self,
        source_map: OccupancyGrid,
        merged_data: List[int],
        merged_width: int,
        merged_height: int,
        merged_min_x: float,
        merged_min_y: float,
        merged_resolution: float,
    ) -> None:
        """Project source map cells into merged grid and combine occupancy values."""
        src_width = int(source_map.info.width)
        src_height = int(source_map.info.height)
        src_res = float(source_map.info.resolution)
        src_origin_x = float(source_map.info.origin.position.x)
        src_origin_y = float(source_map.info.origin.position.y)

        src_data = source_map.data

        for sy in range(src_height):
            for sx in range(src_width):
                src_idx = sy * src_width + sx
                src_val = int(src_data[src_idx])

                # Unknown cells do not contribute information to the merged map.
                if src_val < 0:
                    continue

                # Convert source cell center to world coordinates.
                wx = src_origin_x + (sx + 0.5) * src_res
                wy = src_origin_y + (sy + 0.5) * src_res

                # Convert world coordinates into merged grid indices.
                mx = int((wx - merged_min_x) / merged_resolution)
                my = int((wy - merged_min_y) / merged_resolution)

                # Skip any numerical edge cases that fall outside output bounds.
                if mx < 0 or my < 0 or mx >= merged_width or my >= merged_height:
                    continue

                merged_idx = my * merged_width + mx
                current_val = merged_data[merged_idx]

                # Overlay rule:
                # - If merged cell is unknown, accept first known value.
                # - If already known, keep max occupancy (occupied dominates free).
                if current_val < 0:
                    merged_data[merged_idx] = src_val
                else:
                    merged_data[merged_idx] = max(current_val, src_val)


def main(args=None) -> None:
    """Entry point for ros2 run mapping map_merge_node."""
    rclpy.init(args=args)
    node = MapMergeNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
