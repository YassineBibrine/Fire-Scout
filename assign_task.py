#!/usr/bin/env python3

import sys
from importlib import import_module

import rclpy
from geometry_msgs.msg import Pose
from rclpy.node import Node

# Resolve interface dynamically to avoid IDE env mismatch.
AssignTask = getattr(import_module('firescout_interfaces.srv'), 'AssignTask')

class TaskAssigner(Node):
    def __init__(self):
        super().__init__('task_assigner')
        self.cli = self.create_client(AssignTask, '/coordination/services/assign_task')
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Service not available, waiting...')
        self.req = AssignTask.Request()

    def send_request(self, robot_id, x, y):
        self.req.task_id = f'manual_task_{robot_id}'
        self.req.task_type = 'navigation'
        self.req.target_robot = robot_id
        self.req.target_pose = Pose()
        self.req.target_pose.position.x = float(x)
        self.req.target_pose.position.y = float(y)
        self.req.target_pose.position.z = 0.0
        self.req.target_pose.orientation.w = 1.0
        self.req.priority = 1.0

        future = self.cli.call_async(self.req)
        rclpy.spin_until_future_complete(self, future)
        return future.result()

def main():
    rclpy.init()
    node = TaskAssigner()

    if len(sys.argv) < 4:
        print("Usage: python assign_task.py <robot_id> <x> <y>")
        print("Example: python assign_task.py robot1 2.0 2.0")
        return

    robot_id = sys.argv[1]
    x = sys.argv[2]
    y = sys.argv[3]

    response = node.send_request(robot_id, x, y)
    if response is None:
        node.get_logger().error('AssignTask service returned no response')
    else:
        node.get_logger().info(f'Result: success={response.success}, message="{response.message}"')

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()