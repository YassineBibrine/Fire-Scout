#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import time

class CmdVelTest(Node):
    def __init__(self):
        super().__init__('cmd_vel_test')
        self.pub = self.create_publisher(Twist, '/robot1/cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.publish_cmd)

    def publish_cmd(self):
        twist = Twist()
        twist.linear.x = 0.1  # Small forward velocity
        self.pub.publish(twist)
        self.get_logger().info('Published cmd_vel')

def main():
    rclpy.init()
    node = CmdVelTest()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()