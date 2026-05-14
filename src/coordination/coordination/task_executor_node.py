from __future__ import annotations

import math
from importlib import import_module
from typing import Any, Dict, Optional, cast

import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import Pose, Twist
from nav_msgs.msg import Odometry
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.time import Time
from std_msgs.msg import String
from tf2_ros import Buffer, TransformListener

TaskAssignment = getattr(import_module('firescout_interfaces.msg'), 'TaskAssignment')
try:
    NavigateToPose = getattr(import_module('nav2_msgs.action'), 'NavigateToPose')
except Exception:  # pragma: no cover - optional dependency
    NavigateToPose = None


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


class TaskExecutorNode(Node):
    def __init__(self, **kwargs) -> None:
        super().__init__('task_executor_node', **kwargs)

        self.declare_parameter('robot_ids', ['robot1', 'robot2', 'robot3'])
        self.declare_parameter('control_rate_hz', 10.0)
        self.declare_parameter('linear_gain', 1.0)
        self.declare_parameter('angular_gain', 2.4)
        self.declare_parameter('max_linear_speed', 0.6)
        self.declare_parameter('max_angular_speed', 1.8)
        self.declare_parameter('goal_tolerance_m', 0.25)
        self.declare_parameter('heading_tolerance_rad', 0.2)
        self.declare_parameter('allow_identity_map_to_odom_fallback', True)
        self.declare_parameter('tf_listener_spin_thread', True)
        self.declare_parameter('use_nav2', True)
        self.declare_parameter('nav2_fallback_to_direct', True)
        self.declare_parameter('nav2_action_timeout_sec', 0.2)
        self.declare_parameter('nav2_goal_retry_sec', 1.0)

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
        self._use_nav2 = bool(self.get_parameter('use_nav2').value)
        self._nav2_fallback_to_direct = bool(self.get_parameter('nav2_fallback_to_direct').value)
        self._nav2_action_timeout_sec = max(float(self.get_parameter('nav2_action_timeout_sec').value), 0.0)
        self._nav2_goal_retry_sec = max(float(self.get_parameter('nav2_goal_retry_sec').value), 0.1)

        self._latest_odom: Dict[str, Optional[Odometry]] = {robot_id: None for robot_id in self._robot_ids}
        self._active_task: Dict[str, Optional[Any]] = {robot_id: None for robot_id in self._robot_ids}
        self._avoidance_state: Dict[str, str] = {robot_id: 'FREE' for robot_id in self._robot_ids}
        self._reported_identity_fallback = set()
        self._cmd_vel_publishers = {
            robot_id: self.create_publisher(Twist, f'/{robot_id}/cmd_vel', 10)
            for robot_id in self._robot_ids
        }
        self._nav2_clients: Dict[str, Optional[ActionClient]] = {robot_id: None for robot_id in self._robot_ids}
        self._nav2_goal_handles: Dict[str, Optional[Any]] = {robot_id: None for robot_id in self._robot_ids}
        self._nav2_goal_task_id: Dict[str, Optional[str]] = {robot_id: None for robot_id in self._robot_ids}
        self._nav2_goal_active: Dict[str, bool] = {robot_id: False for robot_id in self._robot_ids}
        self._nav2_last_attempt: Dict[str, float] = {robot_id: 0.0 for robot_id in self._robot_ids}
        self._nav2_warned_unready = set()

        self._nav2_action_type = NavigateToPose
        if self._use_nav2 and self._nav2_action_type is None:
            self.get_logger().warning('nav2_msgs not available; falling back to direct cmd_vel control.')
            self._use_nav2 = False

        if self._use_nav2:
            nav2_action_type = cast(Any, self._nav2_action_type)
            for robot_id in self._robot_ids:
                self._nav2_clients[robot_id] = ActionClient(
                    self,
                    nav2_action_type,
                    f'/{robot_id}/navigate_to_pose',
                )

        self.create_subscription(TaskAssignment, '/coordination/task_assignments', self._task_assignment_callback, 10)
        for robot_id in self._robot_ids:
            self.create_subscription(Odometry, f'/{robot_id}/odom', self._make_odom_callback(robot_id), 10)
            self.create_subscription(
                String,
                f'/{robot_id}/avoidance_state',
                self._make_avoidance_state_callback(robot_id),
                10,
            )

        self._tf_buffer = Buffer()
        self._tf_listener = TransformListener(
            self._tf_buffer,
            self,
            spin_thread=self._tf_listener_spin_thread,
        )
        self.create_timer(1.0 / self._control_rate_hz, self._control_loop)

        self.get_logger().info(f'Task Executor Node started for robots: {", ".join(self._robot_ids)}')

    def _make_odom_callback(self, robot_id: str):
        def _callback(msg: Odometry) -> None:
            self._latest_odom[robot_id] = msg

        return _callback

    def _make_avoidance_state_callback(self, robot_id: str):
        def _cb(msg: String) -> None:
            self._avoidance_state[robot_id] = msg.data

        return _cb

    def _task_assignment_callback(self, msg: Any) -> None:
        robot_id = str(msg.assigned_robot)
        if robot_id not in self._active_task:
            self.get_logger().warning(f'Ignoring task {msg.task_id} for unknown robot {robot_id}')
            return

        self._active_task[robot_id] = msg
        if self._use_nav2:
            if self._nav2_goal_task_id.get(robot_id) != msg.task_id:
                self._cancel_nav2_goal(robot_id)
            self._maybe_send_nav2_goal(robot_id, msg)
        self.get_logger().info(
            f'Received task {msg.task_id} for {robot_id} -> '
            f'({msg.target_pose.position.x:.2f}, {msg.target_pose.position.y:.2f})'
        )

    def _control_loop(self) -> None:
        for robot_id in self._robot_ids:
            assignment = self._active_task.get(robot_id)

            if self._use_nav2:
                if assignment is None:
                    continue
                if self._nav2_goal_active.get(robot_id) and self._nav2_goal_task_id.get(robot_id) == assignment.task_id:
                    continue
                if self._maybe_send_nav2_goal(robot_id, assignment):
                    continue
                if not self._nav2_fallback_to_direct:
                    continue

            if self._avoidance_state.get(robot_id, 'FREE') in ('AVOIDING', 'RECOVERING', 'STUCK'):
                # Safety node is in control — do not publish cmd_vel
                continue

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

            dx = float(goal.position.x) - current_x
            dy = float(goal.position.y) - current_y
            distance = math.hypot(dx, dy)
            heading_error = _normalize_angle(math.atan2(dy, dx) - current_yaw)

            if distance <= self._goal_tolerance_m:
                self._active_task[robot_id] = None
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

    def _cancel_nav2_goal(self, robot_id: str) -> None:
        handle = self._nav2_goal_handles.get(robot_id)
        if handle is None or not self._nav2_goal_active.get(robot_id):
            return

        cancel_future = handle.cancel_goal_async()

        def _on_cancel_done(_future) -> None:
            self._nav2_goal_active[robot_id] = False
            self._nav2_goal_handles[robot_id] = None
            self._nav2_goal_task_id[robot_id] = None

        cancel_future.add_done_callback(_on_cancel_done)

    def _maybe_send_nav2_goal(self, robot_id: str, assignment: Any) -> bool:
        if not self._use_nav2:
            return False

        if self._nav2_action_type is None:
            return False

        client = self._nav2_clients.get(robot_id)
        if client is None:
            return False

        now_sec = float(self.get_clock().now().nanoseconds) / 1e9
        last_attempt = self._nav2_last_attempt.get(robot_id, 0.0)
        if now_sec - last_attempt < self._nav2_goal_retry_sec:
            return False
        self._nav2_last_attempt[robot_id] = now_sec

        if not client.wait_for_server(timeout_sec=self._nav2_action_timeout_sec):
            if robot_id not in self._nav2_warned_unready:
                self.get_logger().warning(
                    f'Nav2 action server not ready for {robot_id}; using fallback control.'
                )
                self._nav2_warned_unready.add(robot_id)
            return False

        self._nav2_warned_unready.discard(robot_id)

        goal = self._nav2_action_type.Goal()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose = assignment.target_pose

        send_future = client.send_goal_async(goal)
        send_future.add_done_callback(
            lambda future, rid=robot_id, task_id=assignment.task_id: self._nav2_goal_response_cb(
                future,
                rid,
                task_id,
            )
        )
        return True

    def _nav2_goal_response_cb(self, future, robot_id: str, task_id: str) -> None:
        goal_handle = future.result()
        if not goal_handle or not goal_handle.accepted:
            self.get_logger().warning(f'Nav2 goal rejected for {robot_id} task {task_id}.')
            self._nav2_goal_active[robot_id] = False
            self._nav2_goal_handles[robot_id] = None
            return

        self._nav2_goal_handles[robot_id] = goal_handle
        self._nav2_goal_active[robot_id] = True
        self._nav2_goal_task_id[robot_id] = task_id

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(
            lambda res_future, rid=robot_id, task=task_id: self._nav2_goal_result_cb(
                res_future,
                rid,
                task,
            )
        )

    def _nav2_goal_result_cb(self, future, robot_id: str, task_id: str) -> None:
        result = future.result()
        status = result.status if result else GoalStatus.STATUS_UNKNOWN

        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info(f'{robot_id} reached task {task_id} via Nav2.')
        else:
            self.get_logger().warning(
                f'{robot_id} Nav2 goal {task_id} completed with status {status}.'
            )

        self._active_task[robot_id] = None
        self._nav2_goal_active[robot_id] = False
        self._nav2_goal_handles[robot_id] = None
        self._nav2_goal_task_id[robot_id] = None


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
