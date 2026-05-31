"""Publish deterministic ESP32-style fire sensor payloads for simulation."""

import math
from importlib import import_module

import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node

SensorData = getattr(import_module('firescout_interfaces.msg'), 'SensorData')

_FIRE_POSITIONS = (
    (3.0, 2.0),
    (2.37, -5.22),
    (4.02, 1.94),
    (6.67, -4.54),
    (-1.33, -5.17),
    (-4.78, 0.06),
)


class DummyEsp32SensorPub(Node):
    """Approximate flame/smoke/gas readings from distance to scenario fires."""

    def __init__(self):
        super().__init__('dummy_esp32_sensor_pub')
        self.declare_parameter('robot_id', 'robot1')
        self.declare_parameter('publish_rate_hz', 5.0)
        if not self.has_parameter('use_sim_time'):
            self.declare_parameter('use_sim_time', True)

        self.robot_id = str(self.get_parameter('robot_id').value)
        publish_rate_hz = max(float(self.get_parameter('publish_rate_hz').value), 0.5)
        self._latest_odom = None

        self.create_subscription(
            Odometry,
            f'/{self.robot_id}/odom',
            self._odom_callback,
            10,
        )
        self._pub = self.create_publisher(
            SensorData,
            f'/{self.robot_id}/esp32/sensors',
            10,
        )
        self.create_timer(1.0 / publish_rate_hz, self._publish_sensor_data)

    def _odom_callback(self, msg: Odometry) -> None:
        self._latest_odom = msg

    def _nearest_fire_distance(self) -> float:
        if self._latest_odom is None:
            return math.inf
        x = float(self._latest_odom.pose.pose.position.x)
        y = float(self._latest_odom.pose.pose.position.y)
        return min(math.hypot(fire_x - x, fire_y - y) for fire_x, fire_y in _FIRE_POSITIONS)

    def _publish_sensor_data(self) -> None:
        distance = self._nearest_fire_distance()
        proximity = max(0.0, min(1.0, 1.0 - distance / 5.0))

        msg = SensorData()
        msg.sensor_type = 'esp32_fire'
        msg.data = [
            1.0 if distance <= 3.0 else 0.0,
            proximity,
            proximity * 0.8,
            25.0 + proximity * 175.0,
        ]
        msg.timestamp = self.get_clock().now().to_msg()
        self._pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = DummyEsp32SensorPub()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
