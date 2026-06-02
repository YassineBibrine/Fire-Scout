from __future__ import annotations

import math
from importlib import import_module
from typing import Any, Dict, Optional

import rclpy
from geometry_msgs.msg import Pose, Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener

TaskAssignment = getattr(import_module('firescout_interfaces.msg'), 'TaskAssignment')


def _yaw_from_quaternion(x: float, y: float, z: float, w: float) -> float:
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    return math.atan2(siny_cosp, cosy_cosp)


def _normalize_angle(angle: float) -> float:
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


def _task_priority(task_type: str) -> int:
    if task_type == 'RESCUE':
        return 2
    if task_type == 'SUPPRESS':
        return 1
    return 0


class TaskExecutorNode(Node):
    def __init__(self, **kwargs) -> None:
        super().__init__('task_executor_node', **kwargs)

        self.declare_parameter('robot_ids', ['robot1', 'robot2', 'robot3'])
        self.declare_parameter('control_rate_hz', 10.0)
        self.declare_parameter('linear_gain', 0.8)
        self.declare_parameter('angular_gain', 2.0)
        self.declare_parameter('max_linear_speed', 0.35)
        self.declare_parameter('max_angular_speed', 1.25)
        self.declare_parameter('goal_tolerance_m', 0.25)
        self.declare_parameter('heading_tolerance_rad', 0.2)
        self.declare_parameter('stuck_timeout_sec', 15.0)
        self.declare_parameter('stuck_progress_threshold_m', 0.2)
        self.declare_parameter('allow_identity_map_to_odom_fallback', True)
        self.declare_parameter('tf_listener_spin_thread', True)

        robot_ids = list(self.get_parameter('robot_ids').value)
        self._robot_ids = [str(robot_id) for robot_id in robot_ids if str(robot_id)] or ['robot1', 'robot2', 'robot3']

        self._control_rate_hz = max(float(self.get_parameter('control_rate_hz').value), 0.1)
        self._linear_gain = float(self.get_parameter('linear_gain').value)
        self._angular_gain = float(self.get_parameter('angular_gain').value)
        self._max_linear_speed = max(float(self.get_parameter('max_linear_speed').value), 0.0)
        self._max_angular_speed = max(float(self.get_parameter('max_angular_speed').value), 0.0)
        self._goal_tolerance_m = max(float(self.get_parameter('goal_tolerance_m').value), 0.0)
        self._heading_tolerance_rad = max(float(self.get_parameter('heading_tolerance_rad').value), 0.0)
        self._allow_identity_map_to_odom_fallback = bool(
            self.get_parameter('allow_identity_map_to_odom_fallback').value
        )
        self._tf_listener_spin_thread = bool(self.get_parameter('tf_listener_spin_thread').value)

        self._latest_odom: Dict[str, Optional[Odometry]] = {robot_id: None for robot_id in self._robot_ids}
        self._active_task: Dict[str, Optional[Any]] = {robot_id: None for robot_id in self._robot_ids}
        self._task_start_time: Dict[str, float] = {}
        self._task_start_distance: Dict[str, float] = {}
        self._task_min_distance: Dict[str, float] = {}
        self._reported_identity_fallback = set()
        self._cmd_vel_publishers = {
            robot_id: self.create_publisher(Twist, f'/{robot_id}/cmd_vel', 10)
            for robot_id in self._robot_ids
        }

        self.create_subscription(TaskAssignment, '/coordination/task_assignments', self._task_assignment_callback, 10)
        for robot_id in self._robot_ids:
            self.create_subscription(Odometry, f'/{robot_id}/odom', self._make_odom_callback(robot_id), 10)

        self._tf_buffer = Buffer()
        self._tf_listener = TransformListener(
            self._tf_buffer,
            self,
            spin_thread=self._tf_listener_spin_thread,
        )
        self.create_timer(1.0 / self._control_rate_hz, self._control_loop)
        self.create_timer(5.0, self._diagnostics_timer)

        self.get_logger().info(f'Task Executor Node started for robots: {", ".join(self._robot_ids)}')

    def _make_odom_callback(self, robot_id: str):
        def _callback(msg: Odometry) -> None:
            self._latest_odom[robot_id] = msg

        return _callback

    def _task_assignment_callback(self, msg: Any) -> None:
        robot_id = str(msg.assigned_robot)
        if robot_id not in self._active_task:
            self.get_logger().warning(f'Ignoring task {msg.task_id} for unknown robot {robot_id}')
            return

        active = self._active_task[robot_id]
        if active is not None:
            active_priority = _task_priority(str(active.task_type))
            incoming_priority = _task_priority(str(msg.task_type))
            if active_priority > incoming_priority:
                self.get_logger().warning(
                    f'Rejecting task {msg.task_id} (type={msg.task_type}, priority={incoming_priority}) '
                    f'for {robot_id}: active task {active.task_id} (type={active.task_type}, '
                    f'priority={active_priority}) has higher priority'
                )
                return

        self._active_task[robot_id] = msg
        now_sec = self.get_clock().now().nanoseconds / 1e9
        self._task_start_time[robot_id] = now_sec
        self._task_min_distance.pop(robot_id, None)
        self._task_start_distance.pop(robot_id, None)
        self.get_logger().info(
            f'Received task {msg.task_id} for {robot_id} -> '
            f'({msg.target_pose.position.x:.2f}, {msg.target_pose.position.y:.2f})'
        )

    def _control_loop(self) -> None:
        for robot_id in self._robot_ids:
            assignment = self._active_task.get(robot_id)
            odom = self._latest_odom.get(robot_id)

            twist = Twist()
            if odom is None:
                continue

            if assignment is None:
                self._cmd_vel_publishers[robot_id].publish(twist)
                continue

            goal = self._transform_goal_to_odom(robot_id, assignment.target_pose)
            if goal is None:
                self._cmd_vel_publishers[robot_id].publish(twist)
                continue

            current_x = float(odom.pose.pose.position.x)
            current_y = float(odom.pose.pose.position.y)
            current_yaw = _yaw_from_quaternion(
                odom.pose.pose.orientation.x,
                odom.pose.pose.orientation.y,
                odom.pose.pose.orientation.z,
                odom.pose.pose.orientation.w,
            )

            if not (math.isfinite(current_x) and math.isfinite(current_y) and math.isfinite(current_yaw)):
                self._cmd_vel_publishers[robot_id].publish(twist)
                continue

            dx = float(goal.position.x) - current_x
            dy = float(goal.position.y) - current_y
            if not (math.isfinite(dx) and math.isfinite(dy)):
                self._cmd_vel_publishers[robot_id].publish(twist)
                continue
            distance = math.hypot(dx, dy)
            heading_error = _normalize_angle(math.atan2(dy, dx) - current_yaw)

            prev_min = self._task_min_distance.get(robot_id, distance)
            self._task_min_distance[robot_id] = min(prev_min, distance)
            if self._task_start_distance.get(robot_id) is None:
                self._task_start_distance[robot_id] = distance

            if distance <= self._goal_tolerance_m:
                self._active_task[robot_id] = None
                self._task_start_time.pop(robot_id, None)
                self._task_start_distance.pop(robot_id, None)
                self._task_min_distance.pop(robot_id, None)
                self._cmd_vel_publishers[robot_id].publish(twist)
                self.get_logger().info(f'{robot_id} reached task {assignment.task_id}')
                continue

            twist.linear.x = min(self._linear_gain * distance, self._max_linear_speed)
            if abs(heading_error) > 1.0:
                twist.linear.x *= 0.35
            twist.angular.z = max(
                min(self._angular_gain * heading_error, self._max_angular_speed),
                -self._max_angular_speed,
            )

            if abs(heading_error) <= self._heading_tolerance_rad:
                twist.angular.z *= 0.5

            self._cmd_vel_publishers[robot_id].publish(twist)

    def _diagnostics_timer(self) -> None:
        stuck_timeout = float(self.get_parameter('stuck_timeout_sec').value)
        stuck_threshold = float(self.get_parameter('stuck_progress_threshold_m').value)
        now_sec = self.get_clock().now().nanoseconds / 1e9
        status_parts = []
        for robot_id in self._robot_ids:
            has_odom = self._latest_odom.get(robot_id) is not None
            has_task = self._active_task.get(robot_id) is not None

            if has_task and robot_id in self._task_start_time:
                elapsed = now_sec - self._task_start_time[robot_id]
                start_dist = self._task_start_distance.get(robot_id)
                min_dist = self._task_min_distance.get(robot_id)
                if elapsed > stuck_timeout and start_dist is not None and min_dist is not None:
                    progress = start_dist - min_dist
                    if progress < stuck_threshold:
                        task = self._active_task[robot_id]
                        self._active_task[robot_id] = None
                        self._task_start_time.pop(robot_id, None)
                        self._task_start_distance.pop(robot_id, None)
                        self._task_min_distance.pop(robot_id, None)
                        self.get_logger().warning(
                            f'{robot_id} STUCK on task {task.task_id}: '
                            f'start_dist={start_dist:.2f}m min_dist={min_dist:.2f}m '
                            f'progress={progress:.2f}m after {elapsed:.0f}s — abandoning'
                        )
                        has_task = False

            status_parts.append(f'{robot_id}(odom={"Y" if has_odom else "N"},task={"Y" if has_task else "N"})')
        sep = ' | '
        self.get_logger().info(f'Executor status: {sep.join(status_parts)}')

    def _transform_goal_to_odom(self, robot_id: str, target_pose: Pose) -> Optional[Pose]:
        target_frame = f'{robot_id}/odom'
        try:
            transform = self._tf_buffer.lookup_transform(target_frame, 'map', Time())
        except Exception as exc:
            if self._allow_identity_map_to_odom_fallback:
                if robot_id not in self._reported_identity_fallback:
                    self.get_logger().warning(
                        f'Using startup identity transform for {target_frame} <- map until SLAM TF is available: {exc}'
                    )
                    self._reported_identity_fallback.add(robot_id)
                goal = Pose()
                goal.position = target_pose.position
                goal.orientation = target_pose.orientation
                return goal
            self.get_logger().warning(f'Waiting for TF {target_frame} <- map: {exc}')
            return None

        translation = transform.transform.translation
        rotation = transform.transform.rotation
        transform_yaw = _yaw_from_quaternion(rotation.x, rotation.y, rotation.z, rotation.w)

        goal = Pose()
        goal.position.x = (
            math.cos(transform_yaw) * float(target_pose.position.x)
            - math.sin(transform_yaw) * float(target_pose.position.y)
            + float(translation.x)
        )
        goal.position.y = (
            math.sin(transform_yaw) * float(target_pose.position.x)
            + math.cos(transform_yaw) * float(target_pose.position.y)
            + float(translation.y)
        )
        goal.position.z = float(target_pose.position.z)
        goal.orientation = target_pose.orientation
        return goal


def main(args=None) -> None:
    rclpy.init(args=args)
    node = TaskExecutorNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
