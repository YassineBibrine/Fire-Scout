"""Publish deterministic ESP32-style fire sensor payloads for simulation."""

import math
import os
from importlib import import_module
import xml.etree.ElementTree as ET

from ament_index_python.packages import get_package_share_directory
import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node

SensorData = getattr(import_module('firescout_interfaces.msg'), 'SensorData')

_FALLBACK_FIRE_POSITIONS = (
    (3.0, 2.0),
    (4.02, 5.7862),
    (6.67, -4.54),
    (-1.8508, -5.17),
    (-7.3638, 0.9669),
    (-8.05, -3.31),
    (7.77, -1.80),
)


def _load_fire_positions_from_world() -> tuple[tuple[float, float], ...]:
    try:
        world_path = os.path.join(
            get_package_share_directory('simulation'),
            'worlds',
            'world_1.sdf',
        )
        root = ET.parse(world_path).getroot()
    except (OSError, ET.ParseError, LookupError):
        return _FALLBACK_FIRE_POSITIONS

    world = root.find('world')
    if world is None:
        return _FALLBACK_FIRE_POSITIONS

    positions = []
    for model in world.findall('model'):
        name = str(model.attrib.get('name', ''))
        if not (name == 'fire_entity' or name.startswith('fire_')):
            continue
        pose_text = model.findtext('pose')
        if not pose_text:
            continue
        parts = pose_text.split()
        if len(parts) < 2:
            continue
        try:
            positions.append((float(parts[0]), float(parts[1])))
        except ValueError:
            continue

    return tuple(positions) or _FALLBACK_FIRE_POSITIONS


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
        self._fire_positions = _load_fire_positions_from_world()

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
        return min(math.hypot(fire_x - x, fire_y - y) for fire_x, fire_y in self._fire_positions)

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
