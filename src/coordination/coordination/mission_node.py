"""ROS 2 mission allocator node for task assignment events."""

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from coordination.task_allocator import assign_task


class MissionNode(Node):
    def __init__(self):
        super().__init__('mission_node')
        self.create_subscription(String, 'coordination/task_bids', self._on_bids, 10)
        self.assignment_pub = self.create_publisher(String, 'coordination/task_assignments', 10)

    def _on_bids(self, msg):
        try:
            payload = json.loads(msg.data)
            task_id = payload['task_id']
            bids = payload['bids']
        except (KeyError, TypeError, json.JSONDecodeError):
            self.get_logger().warning('Invalid task bid payload')
            return

        assignment = assign_task(task_id, bids)
        out = String()
        out.data = json.dumps(assignment)
        self.assignment_pub.publish(out)


def main():
    rclpy.init()
    node = MissionNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
