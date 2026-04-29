from importlib import import_module

import rclpy
from rclpy.node import Node

# Resolve the generated ROS message classes dynamically to avoid static analyzer
# false positives when interface stubs are not discoverable in the IDE env.
AuctionResult = getattr(import_module('firescout_interfaces.msg'), 'AuctionResult')
TaskAssignment = getattr(import_module('firescout_interfaces.msg'), 'TaskAssignment')
AssignTask = getattr(import_module('firescout_interfaces.srv'), 'AssignTask')


class TaskAllocatorNode(Node):

    def __init__(self):

        super().__init__('task_allocator_node')

        self.declare_parameter(
            'use_sim_time',
            True
        )

        self.publisher_ = self.create_publisher(
            TaskAssignment,
            '/coordination/task_assignments',
            10
        )

        self.create_subscription(
            AuctionResult,
            '/coordination/auction_result',
            self.auction_result_callback,
            10
        )

        self.create_service(
            AssignTask,
            '/coordination/services/assign_task',
            self.assign_task_callback
        )

        self.get_logger().info(
            'Task Allocator Node started'
        )

    def auction_result_callback(self, result):

        assignment = self.build_assignment(
            task_id=result.task_id,
            task_type=str(result.task_type),
            target_robot=result.winner_robot_id,
            target_pose=result.target_pose.pose
        )

        self.publisher_.publish(assignment)

    def assign_task_callback(self, request, response):

        assignment = self.build_assignment(
            task_id=request.task_id,
            task_type=request.task_type,
            target_robot=request.target_robot,
            target_pose=request.target_pose
        )

        self.publisher_.publish(assignment)

        response.success = True
        response.message = f"Task {request.task_id} assigned to {request.target_robot}"

        return response

    def build_assignment(self, task_id, task_type, target_robot, target_pose):

        assignment = TaskAssignment()
        assignment.task_id = task_id
        assignment.task_type = task_type
        assignment.assigned_robot = target_robot
        assignment.target_pose = target_pose
        assignment.priority = 0.5
        assignment.estimated_duration = 0.0

        now = self.get_clock().now()
        assignment.assignment_time = now.to_msg()
        assignment.deadline = (now + rclpy.time.Duration(seconds=30.0)).to_msg()

        return assignment


def main(args=None):

    rclpy.init(args=args)

    node = TaskAllocatorNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
