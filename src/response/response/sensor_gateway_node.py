from importlib import import_module

import rclpy
from rclpy.node import Node

SensorData = getattr(import_module('firescout_interfaces.msg'), 'SensorData')
FireSensorAlert = getattr(import_module('firescout_interfaces.msg'), 'FireSensorAlert')

# Sensor types accepted from ESP32 hardware
_VALID_SENSOR_TYPES = frozenset({'fire_sensor', 'esp32_fire', 'esp32'})

# Data array indices
_IDX_FLAME = 0
_IDX_SMOKE = 1
_IDX_GAS = 2
_IDX_TEMP = 3
_MIN_DATA_LEN = 4

# Temperature reference points for normalisation (degrees Celsius)
_TEMP_AMBIENT = 25.0
_TEMP_SPAN = 475.0  # 500 °C ceiling → normalised 1.0


class SensorGatewayNode(Node):
    """
    Bridges raw ESP32 sensor payloads (SensorData) to structured
    FireSensorAlert messages consumed by the fusion pipeline.

    Subscribes : /{robot_id}/esp32/sensors  (SensorData)
    Publishes  : /{robot_id}/fire_sensor_alert  (FireSensorAlert)
    """

    def __init__(self):
        super().__init__('sensor_gateway_node')

        self.declare_parameter('robot_id', 'robot1')
        if not self.has_parameter('use_sim_time'):
            self.declare_parameter('use_sim_time', False)

        self.robot_id = self.get_parameter('robot_id').value

        self._sub = self.create_subscription(
            SensorData,
            f'/{self.robot_id}/esp32/sensors',
            self._sensor_callback,
            10,
        )

        self._pub = self.create_publisher(
            FireSensorAlert,
            f'/{self.robot_id}/fire_sensor_alert',
            10,
        )

        self.get_logger().info(
            f'SensorGatewayNode started for {self.robot_id}'
        )

    # ------------------------------------------------------------------
    # Subscription callback
    # ------------------------------------------------------------------

    def _sensor_callback(self, msg: SensorData) -> None:
        if not self._validate(msg):
            self.get_logger().warn(
                f'Rejected sensor message: type="{msg.sensor_type}" '
                f'data_len={len(msg.data)}'
            )
            return

        alert = self._build_alert(msg)
        self._pub.publish(alert)

        self.get_logger().debug(
            f'FireSensorAlert published: flame={alert.flame_detected} '
            f'smoke={alert.smoke_level:.2f} gas={alert.gas_level:.2f} '
            f'temp={alert.temperature:.1f} risk={alert.normalized_risk:.2f}'
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate(self, msg: SensorData) -> bool:
        if msg.sensor_type not in _VALID_SENSOR_TYPES:
            return False
        if len(msg.data) < _MIN_DATA_LEN:
            return False
        smoke = msg.data[_IDX_SMOKE]
        gas = msg.data[_IDX_GAS]
        # Smoke and gas must be normalised [0, 1]
        if not (0.0 <= smoke <= 1.0 and 0.0 <= gas <= 1.0):
            return False
        return True

    # ------------------------------------------------------------------
    # Alert construction
    # ------------------------------------------------------------------

    def _build_alert(self, msg: SensorData) -> FireSensorAlert:
        flame = float(msg.data[_IDX_FLAME]) > 0.5
        smoke = float(msg.data[_IDX_SMOKE])
        gas = float(msg.data[_IDX_GAS])
        temp = float(msg.data[_IDX_TEMP])

        temp_norm = min(1.0, max(0.0, (temp - _TEMP_AMBIENT) / _TEMP_SPAN))

        # Weighted risk score
        risk = 0.0
        if flame:
            risk += 0.5
        risk += smoke * 0.2
        risk += gas * 0.2
        risk += temp_norm * 0.1
        risk = min(1.0, risk)

        alert = FireSensorAlert()
        alert.robot_id = self.robot_id
        alert.flame_detected = flame
        alert.smoke_level = smoke
        alert.gas_level = gas
        alert.temperature = temp
        alert.normalized_risk = risk
        alert.source_id = msg.sensor_type
        alert.timestamp = msg.timestamp
        return alert


def main(args=None):
    rclpy.init(args=args)
    node = SensorGatewayNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()

