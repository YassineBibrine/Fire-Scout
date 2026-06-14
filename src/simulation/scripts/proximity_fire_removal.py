#!/usr/bin/env python3
import math
import subprocess
import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node


class ProximityFireRemoval(Node):
    """Remove fire_entity from Gazebo when any robot gets within 5m."""

    def __init__(self):
        super().__init__('proximity_fire_removal')

        self.declare_parameter('world_name', 'villa_world')
        self.declare_parameter('robot_ids', ['robot1', 'robot2', 'robot3'])
        self.declare_parameter('proximity_radius', 3.5)
        self.declare_parameter('fire_x', -2.2913)
        self.declare_parameter('fire_y', -4.5792)

        self._world = str(self.get_parameter('world_name').value)
        self._radius = float(self.get_parameter('proximity_radius').value)
        self._fire_x = float(self.get_parameter('fire_x').value)
        self._fire_y = float(self.get_parameter('fire_y').value)
        self._removed = False

        robot_ids = list(self.get_parameter('robot_ids').value)
        for rid in robot_ids:
            rid = str(rid)
            if rid:
                self.create_subscription(Odometry, f'/{rid}/odom',
                                         self._make_callback(rid), 10)
        self._latest_odom = {}

        self.get_logger().info(
            f'Watching for robots within {self._radius}m of fire_entity '
            f'({self._fire_x}, {self._fire_y}) in world {self._world}'
        )

    def _make_callback(self, robot_id):
        def cb(msg):
            self._latest_odom[robot_id] = msg
            self._check_proximity()
        return cb

    def _check_proximity(self):
        if self._removed:
            return
        for robot_id, odom in self._latest_odom.items():
            if odom is None:
                continue
            rx = odom.pose.pose.position.x
            ry = odom.pose.pose.position.y
            d = math.hypot(self._fire_x - rx, self._fire_y - ry)
            if d <= self._radius:
                self.get_logger().info(
                    f'{robot_id} is {d:.2f}m from fire_entity — removing fire_entity'
                )
                self._remove_fire()
                return

    def _remove_fire(self):
        cmd = [
            'gz', 'service',
            '-s', f'/world/{self._world}/remove',
            '--reqtype', 'gz.msgs.Entity',
            '--reptype', 'gz.msgs.Boolean',
            '--timeout', '5000',
            '--req', 'name: "fire_entity" type: 2',
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=8.0)
            output = f'{result.stdout}\n{result.stderr}'.strip()
            if result.returncode == 0 and ('data: true' in output or 'true' in output.lower()):
                self.get_logger().info('fire_entity removed successfully')
                self._removed = True
                self._remove_light()
            else:
                self.get_logger().warning(f'Removal failed: {output}')
        except (OSError, subprocess.TimeoutExpired) as e:
            self.get_logger().error(f'Failed to call Gazebo service: {e}')

    def _remove_light(self):
        cmd = [
            'gz', 'service',
            '-s', f'/world/{self._world}/remove',
            '--reqtype', 'gz.msgs.Entity',
            '--reptype', 'gz.msgs.Boolean',
            '--timeout', '5000',
            '--req', 'name: "fire_glow_1" type: 1',
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=8.0)
            output = f'{result.stdout}\n{result.stderr}'.strip()
            if result.returncode == 0 and ('data: true' in output or 'true' in output.lower()):
                self.get_logger().info('fire_glow_1 light removed')
            else:
                self.get_logger().warning(f'Light removal failed: {output}')
        except (OSError, subprocess.TimeoutExpired) as e:
            self.get_logger().error(f'Failed to remove light: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = ProximityFireRemoval()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
