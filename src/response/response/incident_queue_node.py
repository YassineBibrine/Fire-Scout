"""ROS 2 incident queue node with priority ordering."""

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from response.incident_manager import prioritize_incidents


class IncidentQueueNode(Node):
    def __init__(self):
        super().__init__('incident_queue_node')
        self.queue = []
        self.create_subscription(String, 'response/incidents', self._on_incident, 10)
        self.pub = self.create_publisher(String, 'response/prioritized_incidents', 10)

    def _on_incident(self, msg):
        try:
            incident = json.loads(msg.data)
        except json.JSONDecodeError:
            self.get_logger().warning('Invalid incident payload')
            return

        self.queue.append(incident)
        ordered = prioritize_incidents(self.queue)
        out = String()
        out.data = json.dumps({'incidents': ordered})
        self.pub.publish(out)


def main():
    rclpy.init()
    node = IncidentQueueNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
