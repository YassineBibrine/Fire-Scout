#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from firescout_interfaces.srv import AssignTask
from geometry_msgs.msg import PoseStamped
import sys

class TaskAssigner(Node):
    def __init__(self):
        super().__init__('task_assigner')
        self.cli = self.create_client(AssignTask, '/coordination/services/assign_task')
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Service not available, waiting...')
        self.req = AssignTask.Request()

    def send_request(self, robot_id, x, y):
        self.req.task_id = f'manual_task_{robot_id}'
        self.req.task_type = 1  # Assume 1 is navigation/exploration
        self.req.target_robot = robot_id
        self.req.target_pose = PoseStamped()
        self.req.target_pose.header.frame_id = 'map'
        self.req.target_pose.pose.position.x = float(x)
        self.req.target_pose.pose.position.y = float(y)
        self.req.target_pose.pose.position.z = 0.0
        self.req.target_pose.pose.orientation.w = 1.0
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
    node.get_logger().info(f'Result: success={response.success}, message="{response.message}"')

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()