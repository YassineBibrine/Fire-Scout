from __future__ import annotations

import math
from importlib import import_module
from typing import Any, Dict, Optional

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node

TaskAssignment = getattr(import_module('firescout_interfaces.msg'), 'TaskAssignment')


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
        self.declare_parameter('goal_tolerance_m', 0.35)
        self.declare_parameter('heading_tolerance_rad', 0.45)
        self.declare_parameter('control_period_sec', 0.1)
        self.declare_parameter('max_linear_speed', 0.45)
        self.declare_parameter('max_angular_speed', 1.2)
        self.declare_parameter('linear_gain', 0.8)
        self.declare_parameter('angular_gain', 1.8)
        self.declare_parameter('stuck_timeout_sec', 15.0)
        self.declare_parameter('stuck_progress_threshold_m', 0.2)

        robot_ids = list(self.get_parameter('robot_ids').value)
        self._robot_ids = [str(robot_id) for robot_id in robot_ids if str(robot_id)] or ['robot1', 'robot2', 'robot3']

        self._active_task: Dict[str, Optional[Any]] = {robot_id: None for robot_id in self._robot_ids}
        self._task_start_time: Dict[str, float] = {}
        self._task_start_distance: Dict[str, float] = {}
        self._task_min_distance: Dict[str, float] = {}
        self._latest_odom: Dict[str, Optional[Odometry]] = {robot_id: None for robot_id in self._robot_ids}
        self._task_queue: Dict[str, list] = {robot_id: [] for robot_id in self._robot_ids}

        self._cmd_pubs = {
            robot_id: self.create_publisher(Twist, f'/{robot_id}/cmd_vel', 10)
            for robot_id in self._robot_ids
        }

        self.create_subscription(TaskAssignment, '/coordination/task_assignments', self._task_assignment_callback, 10)
        for robot_id in self._robot_ids:
            self.create_subscription(Odometry, f'/{robot_id}/odom', self._make_odom_callback(robot_id), 10)

        control_period = float(self.get_parameter('control_period_sec').value)
        self.create_timer(control_period, self._control_timer)
        self.create_timer(5.0, self._diagnostics_timer)

        self.get_logger().info(f'Task Executor Node (direct cmd_vel) started for robots: {", ".join(self._robot_ids)}')

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
            if incoming_priority < active_priority:
                self.get_logger().warning(
                    f'Rejecting task {msg.task_id} (type={msg.task_type}, priority={incoming_priority}) '
                    f'for {robot_id}: active task {active.task_id} (type={active.task_type}, '
                    f'priority={active_priority}) has higher priority'
                )
                return
            if incoming_priority == active_priority:
                self._task_queue[robot_id].append(msg)
                self.get_logger().info(
                    f'Task {msg.task_id} queued for {robot_id} (active: {active.task_id})'
                )
                return
            self._cancel_goal(robot_id)

        self._assign_and_send(robot_id, msg)

    def _assign_and_send(self, robot_id: str, task_msg: Any) -> None:
        self._active_task[robot_id] = task_msg
        now_sec = self.get_clock().now().nanoseconds / 1e9
        self._task_start_time[robot_id] = now_sec
        self._task_min_distance.pop(robot_id, None)
        self._task_start_distance.pop(robot_id, None)
        self.get_logger().info(
            f'Driving task {task_msg.task_id} for {robot_id} -> '
            f'({task_msg.target_pose.position.x:.2f}, {task_msg.target_pose.position.y:.2f})'
        )

    def _send_next_from_queue(self, robot_id: str) -> None:
        if self._task_queue[robot_id]:
            next_msg = self._task_queue[robot_id].pop(0)
            self.get_logger().info(
                f'Dequeuing task {next_msg.task_id} for {robot_id}'
            )
            self._assign_and_send(robot_id, next_msg)

    def _cancel_goal(self, robot_id: str) -> None:
        self._publish_stop(robot_id)

    def _abandon_task(self, robot_id: str, reason: str) -> None:
        task = self._active_task.get(robot_id)
        if task is None:
            self._send_next_from_queue(robot_id)
            return
        self._active_task[robot_id] = None
        self._task_start_time.pop(robot_id, None)
        self._task_start_distance.pop(robot_id, None)
        self._task_min_distance.pop(robot_id, None)
        self._publish_stop(robot_id)
        self.get_logger().warning(
            f'{robot_id} abandoning task {task.task_id}: {reason}'
        )
        self._send_next_from_queue(robot_id)

    def _control_timer(self) -> None:
        goal_tolerance = float(self.get_parameter('goal_tolerance_m').value)
        heading_tolerance = float(self.get_parameter('heading_tolerance_rad').value)
        max_linear = float(self.get_parameter('max_linear_speed').value)
        max_angular = float(self.get_parameter('max_angular_speed').value)
        linear_gain = float(self.get_parameter('linear_gain').value)
        angular_gain = float(self.get_parameter('angular_gain').value)

        for robot_id in self._robot_ids:
            task = self._active_task.get(robot_id)
            odom = self._latest_odom.get(robot_id)
            if task is None:
                continue
            if odom is None:
                self._publish_stop(robot_id)
                continue

            pose = odom.pose.pose
            dx = float(task.target_pose.position.x) - float(pose.position.x)
            dy = float(task.target_pose.position.y) - float(pose.position.y)
            distance = math.hypot(dx, dy)
            if not math.isfinite(distance):
                self._publish_stop(robot_id)
                continue

            if self._task_start_distance.get(robot_id) is None:
                self._task_start_distance[robot_id] = distance
            prev_min = self._task_min_distance.get(robot_id)
            self._task_min_distance[robot_id] = distance if prev_min is None else min(prev_min, distance)

            if distance <= goal_tolerance:
                self._active_task[robot_id] = None
                self._task_start_time.pop(robot_id, None)
                self._task_start_distance.pop(robot_id, None)
                self._task_min_distance.pop(robot_id, None)
                self._publish_stop(robot_id)
                self.get_logger().info(f'{robot_id} reached task {task.task_id} with direct cmd_vel')
                self._send_next_from_queue(robot_id)
                continue

            target_heading = math.atan2(dy, dx)
            heading_error = _normalize_angle(target_heading - _yaw_from_odom(odom))

            cmd = Twist()
            if abs(heading_error) < heading_tolerance:
                cmd.linear.x = min(max_linear, linear_gain * distance)
            else:
                cmd.linear.x = 0.0
            cmd.angular.z = max(-max_angular, min(max_angular, angular_gain * heading_error))
            self._cmd_pubs[robot_id].publish(cmd)

    def _publish_stop(self, robot_id: str) -> None:
        self._cmd_pubs[robot_id].publish(Twist())

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
                        self._cancel_goal(robot_id)
                        task = self._active_task[robot_id]
                        self.get_logger().warning(
                            f'{robot_id} STUCK on task {task.task_id if task else "?"}: '
                            f'start_dist={start_dist:.2f}m min_dist={min_dist:.2f}m '
                            f'progress={progress:.2f}m after {elapsed:.0f}s — abandoning'
                        )
                        self._abandon_task(robot_id, 'stuck timeout')
                        has_task = False

            status_parts.append(f'{robot_id}(odom={"Y" if has_odom else "N"},task={"Y" if has_task else "N"})')
        sep = ' | '
        self.get_logger().info(f'Executor status: {sep.join(status_parts)}')


def _yaw_from_odom(odom: Odometry) -> float:
    orientation = odom.pose.pose.orientation
    siny_cosp = 2.0 * (orientation.w * orientation.z + orientation.x * orientation.y)
    cosy_cosp = 1.0 - 2.0 * (orientation.y * orientation.y + orientation.z * orientation.z)
    return math.atan2(siny_cosp, cosy_cosp)


def _normalize_angle(angle: float) -> float:
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


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
