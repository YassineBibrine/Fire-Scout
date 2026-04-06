"""ROS 2 helper node publishing expected SLAM topic contracts."""

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from mapping.slam_runner import expected_slam_topics


class SlamStatusNode(Node):
    def __init__(self):
        super().__init__('slam_status_node')
        robots_csv = str(self.declare_parameter('robot_ids', 'robot1,robot2,robot3').value)
        self.robot_ids = [item.strip() for item in robots_csv.split(',') if item.strip()]
        self.pub = self.create_publisher(String, 'mapping/slam_topics', 10)
        self.create_timer(1.0, self._publish_status)

    def _publish_status(self):
        msg = String()
        msg.data = json.dumps({'topics': expected_slam_topics(self.robot_ids)})
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = SlamStatusNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
