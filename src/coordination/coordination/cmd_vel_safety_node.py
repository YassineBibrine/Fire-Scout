from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Iterable, Optional, Tuple

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from nav_msgs.msg import Odometry
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String


@dataclass(frozen=True)
class SectorClearance:
    front: float
    left: float
    right: float


def _finite_min(values: Iterable[float], default: float) -> float:
    finite_values = [float(value) for value in values if math.isfinite(float(value))]
    return min(finite_values) if finite_values else default


def scan_clearance(scan: LaserScan, front_angle_rad: float) -> SectorClearance:
    """Return minimum scan ranges in front, front-left, and front-right sectors."""
    ranges = list(scan.ranges)
    if not ranges:
        return SectorClearance(front=math.inf, left=math.inf, right=math.inf)

    angle_min = float(scan.angle_min)
    angle_increment = float(scan.angle_increment)
    range_max = float(scan.range_max) if math.isfinite(float(scan.range_max)) else math.inf
    if angle_increment == 0.0:
        return SectorClearance(front=math.inf, left=math.inf, right=math.inf)

    front_values = []
    left_values = []
    right_values = []
    for index, distance in enumerate(ranges):
        angle = math.atan2(
            math.sin(angle_min + index * angle_increment),
            math.cos(angle_min + index * angle_increment),
        )
        if abs(angle) <= front_angle_rad:
            front_values.append(distance)
        elif 0.0 < angle <= 2.0 * front_angle_rad:
            left_values.append(distance)
        elif -2.0 * front_angle_rad <= angle < 0.0:
            right_values.append(distance)

    return SectorClearance(
        front=_finite_min(front_values, range_max),
        left=_finite_min(left_values, range_max),
        right=_finite_min(right_values, range_max),
    )


def limit_twist_for_obstacles(
    command: Twist,
    clearance: Optional[SectorClearance],
    stop_distance_m: float,
    slow_distance_m: float,
    avoidance_turn_speed: float,
    escape_reverse_speed: float,
) -> Twist:
    """Clamp a velocity command using simple lidar obstacle clearances."""
    safe = Twist()
    safe.linear.x = command.linear.x
    safe.linear.y = command.linear.y
    safe.linear.z = command.linear.z
    safe.angular.x = command.angular.x
    safe.angular.y = command.angular.y
    safe.angular.z = command.angular.z

    if clearance is None or safe.linear.x <= 0.0:
        return safe

    if clearance.front <= stop_distance_m:
        safe.linear.x = -abs(escape_reverse_speed)
        turn_direction = 1.0 if clearance.left >= clearance.right else -1.0
        safe.angular.z = turn_direction * max(abs(safe.angular.z), avoidance_turn_speed)
        return safe

    if clearance.front < slow_distance_m:
        span = max(slow_distance_m - stop_distance_m, 1e-6)
        scale = max(0.0, min(1.0, (clearance.front - stop_distance_m) / span))
        safe.linear.x *= scale

    return safe


class AvoidanceState(Enum):
    FREE = auto()
    SLOWING = auto()
    AVOIDING = auto()
    RECOVERING = auto()
    STUCK = auto()


class CmdVelSafetyNode(Node):
    """Filter commanded velocity with a local lidar-based obstacle reflex."""

    def __init__(self) -> None:
        super().__init__('cmd_vel_safety_node')

        self.declare_parameter('robot_id', 'robot1')
        self.declare_parameter('front_angle_deg', 45.0)
        self.declare_parameter('stop_distance_m', 0.55)
        self.declare_parameter('slow_distance_m', 1.1)
        self.declare_parameter('avoidance_turn_speed', 1.15)
        self.declare_parameter('escape_reverse_speed', 0.25)
        self.declare_parameter('min_avoid_duration_sec', 0.8)
        self.declare_parameter('max_avoid_duration_sec', 3.0)
        self.declare_parameter('max_recovery_duration_sec', 5.0)
        self.declare_parameter('max_stuck_rotations', 4)
        self.declare_parameter('stuck_position_threshold', 0.02)
        self.declare_parameter('stuck_check_period_sec', 1.5)
        self.declare_parameter('all_robot_ids', ['robot1', 'robot2', 'robot3'])
        self.declare_parameter('robot_repulsion_distance_m', 0.9)
        self.declare_parameter('robot_repulsion_stop_m', 0.55)

        self._robot_id = str(self.get_parameter('robot_id').value)
        self._front_angle_rad = math.radians(float(self.get_parameter('front_angle_deg').value))
        self._stop_distance_m = max(float(self.get_parameter('stop_distance_m').value), 0.0)
        self._slow_distance_m = max(float(self.get_parameter('slow_distance_m').value), self._stop_distance_m)
        self._avoidance_turn_speed = max(float(self.get_parameter('avoidance_turn_speed').value), 0.0)
        self._escape_reverse_speed = max(float(self.get_parameter('escape_reverse_speed').value), 0.0)
        self._min_avoid_duration_sec = max(float(self.get_parameter('min_avoid_duration_sec').value), 0.0)
        self._max_avoid_duration_sec = max(float(self.get_parameter('max_avoid_duration_sec').value), 0.0)
        self._max_recovery_duration_sec = max(float(self.get_parameter('max_recovery_duration_sec').value), 0.0)
        self._max_stuck_rotations = max(int(self.get_parameter('max_stuck_rotations').value), 0)
        self._stuck_position_threshold = max(float(self.get_parameter('stuck_position_threshold').value), 0.0)
        self._stuck_check_period_sec = max(float(self.get_parameter('stuck_check_period_sec').value), 0.1)

        all_robot_ids = list(self.get_parameter('all_robot_ids').value)
        self._repulsion_distance = float(self.get_parameter('robot_repulsion_distance_m').value)
        self._repulsion_stop = float(self.get_parameter('robot_repulsion_stop_m').value)
        self._peer_robot_ids = [robot_id for robot_id in all_robot_ids if robot_id != self._robot_id]

        self._latest_clearance: Optional[SectorClearance] = None
        self._latest_cmd: Optional[Twist] = None
        self._latest_position: Optional[Tuple[float, float]] = None
        self._stuck_reference_position: Optional[Tuple[float, float]] = None

        self._own_x = 0.0
        self._own_y = 0.0
        self._own_yaw = 0.0
        self._peer_positions: Dict[str, Optional[Tuple[float, float]]] = {
            robot_id: None for robot_id in self._peer_robot_ids
        }

        now = self.get_clock().now()
        self._state = AvoidanceState.FREE
        self._state_enter_time = now
        self._avoidance_start = now
        self._recovery_start = now

        self._stuck_phase = 'stop'
        self._stuck_phase_start = now
        self._stuck_rotation_count = 0
        self._stuck_rotation_direction = 1.0
        self._stuck_error_logged = False

        self._safe_pub = self.create_publisher(Twist, f'/{self._robot_id}/cmd_vel_safe', 10)
        self._avoidance_state_pub = self.create_publisher(String, f'/{self._robot_id}/avoidance_state', 10)

        self.create_subscription(Twist, f'/{self._robot_id}/cmd_vel', self._cmd_callback, 10)
        self.create_subscription(
            LaserScan,
            f'/{self._robot_id}/scan',
            self._scan_callback,
            qos_profile_sensor_data,
        )
        self.create_subscription(Odometry, f'/{self._robot_id}/odom', self._odom_callback, 10)
        for peer_id in self._peer_robot_ids:
            self.create_subscription(
                Odometry,
                f'/{peer_id}/odom',
                self._make_peer_odom_callback(peer_id),
                10,
            )

        self.create_timer(0.1, self._avoidance_loop)
        self.create_timer(0.5, self._publish_avoidance_state)
        self.create_timer(self._stuck_check_period_sec, self._stuck_check)

        self.get_logger().info(
            f'CmdVelSafetyNode started for {self._robot_id}: '
            f'/{self._robot_id}/cmd_vel -> /{self._robot_id}/cmd_vel_safe'
        )

    def _scan_callback(self, msg: LaserScan) -> None:
        self._latest_clearance = scan_clearance(msg, self._front_angle_rad)
        self._update_state(self.get_clock().now())

    def _odom_callback(self, msg: Odometry) -> None:
        position = msg.pose.pose.position
        self._latest_position = (float(position.x), float(position.y))
        self._own_x = float(position.x)
        self._own_y = float(position.y)
        orientation = msg.pose.pose.orientation
        siny = 2.0 * (orientation.w * orientation.z + orientation.x * orientation.y)
        cosy = 1.0 - 2.0 * (orientation.y * orientation.y + orientation.z * orientation.z)
        self._own_yaw = math.atan2(siny, cosy)

    def _make_peer_odom_callback(self, peer_id: str):
        def _cb(msg: Odometry) -> None:
            self._peer_positions[peer_id] = (
                float(msg.pose.pose.position.x),
                float(msg.pose.pose.position.y),
            )

        return _cb

    def _cmd_callback(self, msg: Twist) -> None:
        self._latest_cmd = msg
        if self._state in (AvoidanceState.AVOIDING, AvoidanceState.RECOVERING, AvoidanceState.STUCK):
            return

        self._update_state(self.get_clock().now())
        if self._state in (AvoidanceState.AVOIDING, AvoidanceState.RECOVERING, AvoidanceState.STUCK):
            return

        clearance = self._merge_clearances(
            self._latest_clearance,
            self._compute_robot_clearance(),
        )

        safe = limit_twist_for_obstacles(
            msg,
            clearance,
            self._stop_distance_m,
            self._slow_distance_m,
            self._avoidance_turn_speed,
            self._escape_reverse_speed,
        )
        self._safe_pub.publish(safe)

    def _set_state(self, new_state: AvoidanceState, now) -> None:
        if new_state == self._state:
            return

        self._state = new_state
        self._state_enter_time = now
        if new_state == AvoidanceState.AVOIDING:
            self._avoidance_start = now
        elif new_state == AvoidanceState.RECOVERING:
            self._recovery_start = now
        elif new_state == AvoidanceState.STUCK:
            self._stuck_phase = 'stop'
            self._stuck_phase_start = now
            self._stuck_rotation_count = 0
            self._stuck_rotation_direction = 1.0
            self._stuck_error_logged = False
        if new_state not in (AvoidanceState.AVOIDING, AvoidanceState.RECOVERING):
            self._stuck_reference_position = None

    def _elapsed_sec(self, now, start) -> float:
        return max(0.0, float((now - start).nanoseconds) / 1e9)

    def _update_state(self, now) -> None:
        clearance = self._merge_clearances(
            self._latest_clearance,
            self._compute_robot_clearance(),
        )
        if clearance is None:
            return

        if self._state == AvoidanceState.FREE:
            if clearance.front <= self._stop_distance_m:
                self._set_state(AvoidanceState.AVOIDING, now)
            elif clearance.front < self._slow_distance_m:
                self._set_state(AvoidanceState.SLOWING, now)
        elif self._state == AvoidanceState.SLOWING:
            if clearance.front <= self._stop_distance_m:
                self._set_state(AvoidanceState.AVOIDING, now)
            elif clearance.front >= self._slow_distance_m:
                self._set_state(AvoidanceState.FREE, now)
        elif self._state == AvoidanceState.AVOIDING:
            avoidance_elapsed = self._elapsed_sec(now, self._avoidance_start)
            if (
                clearance.front > self._slow_distance_m
                and avoidance_elapsed >= self._min_avoid_duration_sec
            ):
                self._set_state(AvoidanceState.FREE, now)
            elif (
                avoidance_elapsed >= self._max_avoid_duration_sec
                and clearance.front <= self._stop_distance_m
            ):
                self._set_state(AvoidanceState.RECOVERING, now)
        elif self._state == AvoidanceState.RECOVERING:
            recovery_elapsed = self._elapsed_sec(now, self._recovery_start)
            if clearance.front > self._slow_distance_m:
                self._set_state(AvoidanceState.FREE, now)
            elif recovery_elapsed >= self._max_recovery_duration_sec:
                self._set_state(AvoidanceState.STUCK, now)
        elif self._state == AvoidanceState.STUCK:
            if clearance.front > self._slow_distance_m:
                self._set_state(AvoidanceState.FREE, now)

    def _avoidance_loop(self) -> None:
        now = self.get_clock().now()
        self._update_state(now)

        if self._state == AvoidanceState.AVOIDING:
            if not self._i_have_avoidance_priority():
                twist = Twist()
                self._safe_pub.publish(twist)
                return
            twist = self._avoidance_twist()
            self._safe_pub.publish(twist)
        elif self._state == AvoidanceState.RECOVERING:
            twist = self._recovery_twist()
            self._safe_pub.publish(twist)
        elif self._state == AvoidanceState.STUCK:
            twist = self._stuck_twist(now)
            self._safe_pub.publish(twist)

    def _avoidance_twist(self) -> Twist:
        clearance = self._merge_clearances(
            self._latest_clearance,
            self._compute_robot_clearance(),
        )
        turn_direction = 1.0
        if clearance is not None:
            turn_direction = 1.0 if clearance.left >= clearance.right else -1.0

        twist = Twist()
        twist.linear.x = -abs(self._escape_reverse_speed)
        twist.angular.z = turn_direction * self._avoidance_turn_speed
        return twist

    def _recovery_twist(self) -> Twist:
        clearance = self._merge_clearances(
            self._latest_clearance,
            self._compute_robot_clearance(),
        )
        turn_direction = 1.0
        if clearance is not None:
            turn_direction = 1.0 if clearance.left >= clearance.right else -1.0

        twist = Twist()
        twist.linear.x = 0.0
        twist.angular.z = turn_direction * self._avoidance_turn_speed
        return twist

    def _stuck_twist(self, now) -> Twist:
        clearance = self._merge_clearances(
            self._latest_clearance,
            self._compute_robot_clearance(),
        )
        if clearance is not None and clearance.front > self._slow_distance_m:
            self._set_state(AvoidanceState.FREE, now)
            return Twist()

        twist = Twist()
        if self._stuck_rotation_count >= self._max_stuck_rotations:
            if not self._stuck_error_logged:
                self.get_logger().error('Max stuck rotations exceeded; holding position.')
                self._stuck_error_logged = True
            return twist

        phase_elapsed = self._elapsed_sec(now, self._stuck_phase_start)
        if self._stuck_phase == 'stop':
            if phase_elapsed >= 1.5:
                self._stuck_phase = 'rotate'
                self._stuck_phase_start = now
                attempt = self._stuck_rotation_count + 1
                self.get_logger().warning(f'Stuck recovery rotation attempt {attempt}.')
            return twist

        twist.angular.z = self._stuck_rotation_direction * self._avoidance_turn_speed
        if phase_elapsed >= 3.0:
            self._stuck_rotation_count += 1
            self._stuck_rotation_direction *= -1.0
            self._stuck_phase = 'stop'
            self._stuck_phase_start = now
        return twist

    def _stuck_check(self) -> None:
        if self._state not in (AvoidanceState.AVOIDING, AvoidanceState.RECOVERING):
            self._stuck_reference_position = None
            return

        if self._latest_position is None:
            return

        if self._stuck_reference_position is None:
            self._stuck_reference_position = self._latest_position
            return

        dx = self._latest_position[0] - self._stuck_reference_position[0]
        dy = self._latest_position[1] - self._stuck_reference_position[1]
        if math.hypot(dx, dy) < self._stuck_position_threshold:
            self._set_state(AvoidanceState.STUCK, self.get_clock().now())
        else:
            self._stuck_reference_position = self._latest_position

    def _publish_avoidance_state(self) -> None:
        msg = String()
        msg.data = self._state.name
        self._avoidance_state_pub.publish(msg)

    def _compute_robot_clearance(self) -> Optional[SectorClearance]:
        """
        Compute a virtual SectorClearance from peer robot positions.
        Returns None if no peer is close enough to matter.
        Returns a SectorClearance with reduced values in the direction
        of the closest peer robot if one is within repulsion_distance.
        """
        closest_distance = math.inf
        closest_bearing_robot = 0.0

        for peer_id, pos in self._peer_positions.items():
            if pos is None:
                continue

            peer_x, peer_y = pos
            dx = peer_x - self._own_x
            dy = peer_y - self._own_y
            distance = math.hypot(dx, dy)

            if distance >= self._repulsion_distance:
                continue

            world_bearing = math.atan2(dy, dx)
            robot_bearing = world_bearing - self._own_yaw
            while robot_bearing > math.pi:
                robot_bearing -= 2.0 * math.pi
            while robot_bearing < -math.pi:
                robot_bearing += 2.0 * math.pi

            if distance < closest_distance:
                closest_distance = distance
                closest_bearing_robot = robot_bearing

        if closest_distance == math.inf:
            return None

        front = math.inf
        left = math.inf
        right = math.inf

        abs_bearing = abs(closest_bearing_robot)

        if abs_bearing <= self._front_angle_rad:
            front = closest_distance
        elif closest_bearing_robot > 0:
            left = closest_distance
        else:
            right = closest_distance

        return SectorClearance(front=front, left=left, right=right)

    def _merge_clearances(
        self,
        lidar: Optional[SectorClearance],
        robot: Optional[SectorClearance],
    ) -> Optional[SectorClearance]:
        """
        Return the element-wise minimum of lidar and robot clearances.
        A None clearance means no obstacle in that source — ignore it.
        """
        if lidar is None and robot is None:
            return None
        if lidar is None:
            return robot
        if robot is None:
            return lidar
        return SectorClearance(
            front=min(lidar.front, robot.front),
            left=min(lidar.left, robot.left),
            right=min(lidar.right, robot.right),
        )

    def _i_have_avoidance_priority(self) -> bool:
        """
        Lexicographically smaller robot_id yields to larger.
        robot1 < robot2 < robot3
        robot3 always has priority and goes first.
        robot1 always yields and waits.
        """
        for peer_id, pos in self._peer_positions.items():
            if pos is None:
                continue
            dx = pos[0] - self._own_x
            dy = pos[1] - self._own_y
            distance = math.hypot(dx, dy)
            if distance < self._repulsion_stop:
                if self._robot_id < peer_id:
                    return False
        return True


def main(args=None) -> None:
    rclpy.init(args=args)
    node = CmdVelSafetyNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
