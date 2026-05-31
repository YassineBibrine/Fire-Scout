"""Mock camera inference node for Phase 2 hybrid simulation testing.

This node simulates the output of a real camera_inference_node by using
known scenario entity positions (fire at (3.0, 2.0) and human victims at
(-3.0, 4.0), (-1.5, -3.0), (2.0, -1.5)) and each robot's odometry to
decide whether the entity would be visible in the robot's forward-facing
camera FOV.

Published topic per robot:
  /<robot_id>/camera_detections  →  firescout_interfaces/msg/VisionDetectionArray

Behaviour:
- Deterministic: same robot pose → same detections.
- Lightweight: pure Python geometry, no image processing.
- Namespace-aware: one publisher per configured robot_id.
- Suitable for CI integration tests without a running Gazebo instance.
"""

from importlib import import_module
import math
from typing import Any, Callable, cast

from geometry_msgs.msg import Pose
import rclpy
from nav_msgs.msg import Odometry
from rclpy.publisher import Publisher
from rclpy.node import Node

# Resolve generated message types dynamically to avoid IDE false positives
# when interface stubs are not available outside of the ROS environment.
_interfaces_msg = import_module('firescout_interfaces.msg')
VisionDetectionArray = cast(Any, getattr(_interfaces_msg, 'VisionDetectionArray'))
Detection = cast(Any, getattr(_interfaces_msg, 'Detection'))


# ---------------------------------------------------------------------------
# Scenario entity definitions (deterministic, matches world_1.sdf Phase 2)
# ---------------------------------------------------------------------------

_SCENARIO_ENTITIES = [
    # (world_x, world_y, class_label, base_confidence)
    (3.0,   2.0,  'fire',  0.88),
    (-3.0,  4.0,  'human', 0.82),
    (-1.5, -3.0,  'human', 0.79),
    (2.0,  -1.5,  'human', 0.75),
]

# Camera parameters (match SDF sensor definition)
_CAMERA_FOV_RAD = 1.047      # ~60 degrees horizontal FOV
_CAMERA_MAX_RANGE_M = 6.0    # entities beyond this distance are not detected
_CAMERA_MIN_RANGE_M = 0.3    # minimum detection distance (too close = no detection)

# Camera is mounted 0.10 m in front of base_link and 0.15 m above it.
_CAMERA_FORWARD_OFFSET = 0.10


def _yaw_from_quaternion(x: float, y: float, z: float, w: float) -> float:
    """Extract 2D yaw angle from a quaternion."""
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    return math.atan2(siny_cosp, cosy_cosp)


def _entity_in_fov(
    robot_x: float, robot_y: float, robot_yaw: float,
    entity_x: float, entity_y: float,
) -> tuple[bool, float, float]:
    """Return (visible, bearing_rad, distance_m) for an entity from robot frame."""
    dx = entity_x - robot_x
    dy = entity_y - robot_y
    distance = math.hypot(dx, dy)

    if distance < _CAMERA_MIN_RANGE_M or distance > _CAMERA_MAX_RANGE_M:
        return False, 0.0, distance

    # Bearing relative to robot heading
    absolute_bearing = math.atan2(dy, dx)
    relative_bearing = absolute_bearing - robot_yaw

    # Normalise to [-pi, pi]
    while relative_bearing > math.pi:
        relative_bearing -= 2.0 * math.pi
    while relative_bearing < -math.pi:
        relative_bearing += 2.0 * math.pi

    half_fov = _CAMERA_FOV_RAD / 2.0
    visible = abs(relative_bearing) <= half_fov

    return visible, relative_bearing, distance


def _project_to_pixel(bearing_rad: float, distance_m: float) -> list[float]:
    """Project world-space bearing + distance to approximate pixel bounding box.

    Produces a plausible but synthetic 640x480 bounding box.
    Object size estimate: 0.5 m at 1 m distance → ~320 px; scales with 1/d.
    """
    # Horizontal centre pixel
    cx = 320.0 + (bearing_rad / (_CAMERA_FOV_RAD / 2.0)) * 320.0
    cy = 240.0  # Approximate: assume entity roughly at horizon height

    # Apparent size in pixels (simplistic pinhole estimate)
    apparent_half_width = max(5.0, min(160.0, 160.0 / max(distance_m, 0.5)))
    apparent_half_height = apparent_half_width * 1.5  # Taller than wide for humans

    x_min = max(0.0, cx - apparent_half_width)
    y_min = max(0.0, cy - apparent_half_height)
    x_max = min(640.0, cx + apparent_half_width)
    y_max = min(480.0, cy + apparent_half_height)

    return [x_min, y_min, x_max, y_max]


class MockCameraInferenceNode(Node):
    """Simulates camera detections from known scenario entity positions."""

    def __init__(self) -> None:
        super().__init__('mock_camera_inference_node')

        self.declare_parameter('robot_ids', ['robot1', 'robot2', 'robot3'])
        self.declare_parameter('publish_rate_hz', 5.0)
        self.declare_parameter('confidence_jitter', 0.05)
        if not self.has_parameter('use_sim_time'):
            self.declare_parameter('use_sim_time', True)

        robot_ids_value = self.get_parameter('robot_ids').value
        robot_ids_param = robot_ids_value if isinstance(robot_ids_value, list) else []
        self._robot_ids = [str(r) for r in robot_ids_param if r] or ['robot1', 'robot2', 'robot3']

        publish_rate_hz = max(float(self.get_parameter('publish_rate_hz').value), 0.5)
        self._confidence_jitter = float(self.get_parameter('confidence_jitter').value)

        # Per-robot latest odometry (used for FOV computation)
        self._latest_odom: dict[str, Odometry | None] = {r: None for r in self._robot_ids}

        # Per-robot VisionDetectionArray publisher
        self._publishers: dict[str, Publisher[Any]] = {}
        for robot_id in self._robot_ids:
            self._publishers[robot_id] = self.create_publisher(
                VisionDetectionArray,
                f'/{robot_id}/camera_detections',
                10,
            )
            self.create_subscription(
                Odometry,
                f'/{robot_id}/odom',
                self._make_odom_callback(robot_id),
                10,
            )

        self.create_timer(1.0 / publish_rate_hz, self._publish_all)

        self.get_logger().info(
            f'MockCameraInferenceNode started for robots: {", ".join(self._robot_ids)}'
        )

    def _make_odom_callback(self, robot_id: str) -> Callable[[Odometry], None]:
        def _cb(msg: Odometry) -> None:
            self._latest_odom[robot_id] = msg
        return _cb

    def _publish_all(self) -> None:
        for robot_id in self._robot_ids:
            msg = self._build_detection_array(robot_id)
            self._publishers[robot_id].publish(msg)

    def _build_detection_array(self, robot_id: str) -> Any:
        now = self.get_clock().now().to_msg()
        arr = VisionDetectionArray()
        arr.robot_id = robot_id
        arr.camera_id = f'{robot_id}_camera_front'
        arr.timestamp = now

        odom = self._latest_odom.get(robot_id)
        if odom is None:
            # No odometry yet: return empty detection array.
            arr.detections = []
            return arr

        robot_x = float(odom.pose.pose.position.x)
        robot_y = float(odom.pose.pose.position.y)
        robot_yaw = _yaw_from_quaternion(
            odom.pose.pose.orientation.x,
            odom.pose.pose.orientation.y,
            odom.pose.pose.orientation.z,
            odom.pose.pose.orientation.w,
        )

        detections = []
        for (ex, ey, label, base_conf) in _SCENARIO_ENTITIES:
            visible, bearing, distance = _entity_in_fov(robot_x, robot_y, robot_yaw, ex, ey)
            if not visible:
                continue

            # Confidence decreases with distance; clamp to [0.05, 0.99]
            distance_factor = max(0.1, 1.0 - (distance / _CAMERA_MAX_RANGE_M) * 0.5)
            confidence = max(0.05, min(0.99, base_conf * distance_factor))

            det = Detection()
            det.class_label = label
            det.confidence = float(confidence)
            det.bounding_box = _project_to_pixel(bearing, distance)

            # Estimated pose in robot frame (simplified: entity at (distance, 0, 0))
            est_pose = Pose()
            est_pose.position.x = distance * math.cos(bearing)
            est_pose.position.y = distance * math.sin(bearing)
            est_pose.position.z = 0.0
            est_pose.orientation.w = 1.0
            det.estimated_pose = est_pose

            detections.append(det)

        arr.detections = detections
        return arr


def main(args=None) -> None:
    rclpy.init(args=args)
    node = MockCameraInferenceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
