"""ROS 2 dummy heartbeat publisher."""

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class HeartbeatPubNode(Node):
    def __init__(self):
        super().__init__('dummy_heartbeat_pub')
        self.pub = self.create_publisher(String, 'heartbeat', 10)
        self.robot_id = str(self.declare_parameter('robot_id', 'robot1').value)
        self.create_timer(1.0, self._tick)

    def _tick(self):
        now_s = self.get_clock().now().nanoseconds / 1e9
        msg = String()
        msg.data = json.dumps({'robot_id': self.robot_id, 'timestamp_s': now_s})
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = HeartbeatPubNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
