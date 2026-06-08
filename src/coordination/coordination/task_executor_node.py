from __future__ import annotations

import math
from importlib import import_module
from typing import Any, Dict, Optional

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import Odometry
from rclpy.action import ActionClient
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
        self.declare_parameter('stuck_timeout_sec', 15.0)
        self.declare_parameter('stuck_progress_threshold_m', 0.2)

        robot_ids = list(self.get_parameter('robot_ids').value)
        self._robot_ids = [str(robot_id) for robot_id in robot_ids if str(robot_id)] or ['robot1', 'robot2', 'robot3']

        self._active_task: Dict[str, Optional[Any]] = {robot_id: None for robot_id in self._robot_ids}
        self._goal_handle: Dict[str, Optional[Any]] = {robot_id: None for robot_id in self._robot_ids}
        self._task_start_time: Dict[str, float] = {}
        self._task_start_distance: Dict[str, float] = {}
        self._task_min_distance: Dict[str, float] = {}
        self._latest_odom: Dict[str, Optional[Odometry]] = {robot_id: None for robot_id in self._robot_ids}
        self._task_queue: Dict[str, list] = {robot_id: [] for robot_id in self._robot_ids}

        self._nav_clients: Dict[str, ActionClient] = {
            robot_id: ActionClient(self, NavigateToPose, f'/{robot_id}/navigate_to_pose')
            for robot_id in self._robot_ids
        }

        self.create_subscription(TaskAssignment, '/coordination/task_assignments', self._task_assignment_callback, 10)
        for robot_id in self._robot_ids:
            self.create_subscription(Odometry, f'/{robot_id}/odom', self._make_odom_callback(robot_id), 10)

        self.create_timer(5.0, self._diagnostics_timer)

        self.get_logger().info(f'Task Executor Node (Nav2) started for robots: {", ".join(self._robot_ids)}')

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
            f'Sending task {task_msg.task_id} for {robot_id} -> '
            f'({task_msg.target_pose.position.x:.2f}, {task_msg.target_pose.position.y:.2f})'
        )

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = PoseStamped()
        goal_msg.pose.header.frame_id = f'{robot_id}/map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose = task_msg.target_pose

        if not self._nav_clients[robot_id].wait_for_server(timeout_sec=30.0):
            self.get_logger().warning(
                f'Nav2 navigate_to_pose server not available for {robot_id} after 30s. '
                f'Task {task_msg.task_id} will be dropped.'
            )
            self._active_task[robot_id] = None
            return
        send_goal_future = self._nav_clients[robot_id].send_goal_async(
            goal_msg, feedback_callback=self._make_feedback_callback(robot_id)
        )
        send_goal_future.add_done_callback(
            self._make_goal_response_callback(robot_id, task_msg.task_id)
        )

    def _send_next_from_queue(self, robot_id: str) -> None:
        if self._task_queue[robot_id]:
            next_msg = self._task_queue[robot_id].pop(0)
            self.get_logger().info(
                f'Dequeuing task {next_msg.task_id} for {robot_id}'
            )
            self._assign_and_send(robot_id, next_msg)

    def _make_goal_response_callback(self, robot_id: str, expected_task_id: str):
        def _callback(future):
            goal_handle = future.result()
            if not goal_handle.accepted:
                self.get_logger().warning(f'{robot_id} NavigateToPose goal rejected')
                self._abandon_task(robot_id, 'goal rejected')
                return
            self._goal_handle[robot_id] = goal_handle
            result_future = goal_handle.get_result_async()
            result_future.add_done_callback(self._make_result_callback(robot_id, expected_task_id))

        return _callback

    def _make_result_callback(self, robot_id: str, expected_task_id: str):
        def _callback(future):
            current = self._active_task.get(robot_id)
            if current is None or current.task_id != expected_task_id:
                return
            self._goal_handle[robot_id] = None
            result = future.result()
            if result.status == 4:  # SUCCEEDED
                self._active_task[robot_id] = None
                self._task_start_time.pop(robot_id, None)
                self._task_start_distance.pop(robot_id, None)
                self._task_min_distance.pop(robot_id, None)
                self.get_logger().info(
                    f'{robot_id} reached task {expected_task_id} via Nav2'
                )
                self._send_next_from_queue(robot_id)
            else:
                self._abandon_task(robot_id, f'Nav2 result status={result.status}')

        return _callback

    def _make_feedback_callback(self, robot_id: str):
        def _callback(feedback_msg):
            feedback = feedback_msg.feedback
            distance = feedback.distance_remaining
            if not math.isfinite(distance):
                return
            prev_min = self._task_min_distance.get(robot_id)
            if prev_min is None:
                prev_min = distance
            self._task_min_distance[robot_id] = min(prev_min, distance)
            if self._task_start_distance.get(robot_id) is None:
                self._task_start_distance[robot_id] = distance

        return _callback

    def _cancel_goal(self, robot_id: str) -> None:
        goal_handle = self._goal_handle.get(robot_id)
        if goal_handle is not None:
            cancel_future = goal_handle.cancel_goal_async()
            cancel_future.add_done_callback(lambda f: None)
            self._goal_handle[robot_id] = None

    def _abandon_task(self, robot_id: str, reason: str) -> None:
        task = self._active_task.get(robot_id)
        if task is None:
            self._send_next_from_queue(robot_id)
            return
        self._active_task[robot_id] = None
        self._task_start_time.pop(robot_id, None)
        self._task_start_distance.pop(robot_id, None)
        self._task_min_distance.pop(robot_id, None)
        self.get_logger().warning(
            f'{robot_id} abandoning task {task.task_id}: {reason}'
        )
        self._send_next_from_queue(robot_id)

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
