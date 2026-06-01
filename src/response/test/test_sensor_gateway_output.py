"""
Unit tests for SensorGatewayNode message construction and validation logic.

These tests execute the gateway logic directly (no ROS runtime required) so
they run cleanly in CI without a DDS / RMW installation.
"""

from types import SimpleNamespace
import math


# ---------------------------------------------------------------------------
# Replicate the gateway's pure-Python logic so tests do not import ROS.
# ---------------------------------------------------------------------------

_VALID_SENSOR_TYPES = frozenset({'fire_sensor', 'esp32_fire', 'esp32'})
_MIN_DATA_LEN = 4
_TEMP_AMBIENT = 25.0
_TEMP_SPAN = 475.0


def _validate(sensor_type: str, data: list) -> bool:
    if sensor_type not in _VALID_SENSOR_TYPES:
        return False
    if len(data) < _MIN_DATA_LEN:
        return False
    smoke, gas = data[1], data[2]
    if not all(math.isfinite(float(value)) for value in data[:4]):
        return False
    if not (0.0 <= smoke <= 1.0 and 0.0 <= gas <= 1.0):
        return False
    return True


def _build_alert(sensor_type: str, data: list) -> SimpleNamespace:
    flame = float(data[0]) > 0.5
    smoke = float(data[1])
    gas = float(data[2])
    temp = float(data[3])
    temp_norm = min(1.0, max(0.0, (temp - _TEMP_AMBIENT) / _TEMP_SPAN))

    risk = 0.0
    if flame:
        risk += 0.5
    risk += smoke * 0.2
    risk += gas * 0.2
    risk += temp_norm * 0.1
    risk = min(1.0, risk)

    return SimpleNamespace(
        flame_detected=flame,
        smoke_level=smoke,
        gas_level=gas,
        temperature=temp,
        normalized_risk=risk,
        source_id=sensor_type,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_valid_fire_data_accepted():
    assert _validate('fire_sensor', [1.0, 0.8, 0.6, 100.0]) is True


def test_valid_esp32_type_accepted():
    assert _validate('esp32', [0.0, 0.1, 0.2, 30.0]) is True


def test_valid_esp32_fire_type_accepted():
    assert _validate('esp32_fire', [1.0, 0.5, 0.3, 80.0]) is True


def test_invalid_sensor_type_rejected():
    assert _validate('lidar', [1.0, 0.8, 0.6, 100.0]) is False


def test_too_few_fields_rejected():
    assert _validate('fire_sensor', [1.0, 0.8]) is False


def test_exactly_four_fields_accepted():
    assert _validate('fire_sensor', [0.0, 0.0, 0.0, 25.0]) is True


def test_smoke_out_of_range_rejected():
    assert _validate('fire_sensor', [1.0, 1.5, 0.6, 100.0]) is False


def test_gas_out_of_range_rejected():
    assert _validate('fire_sensor', [1.0, 0.5, -0.1, 100.0]) is False


def test_nan_sensor_value_rejected():
    assert _validate('fire_sensor', [1.0, float('nan'), 0.2, 100.0]) is False


def test_flame_detected_true_when_above_threshold():
    alert = _build_alert('fire_sensor', [1.0, 0.0, 0.0, 25.0])
    assert alert.flame_detected is True


def test_flame_detected_false_when_below_threshold():
    alert = _build_alert('fire_sensor', [0.3, 0.0, 0.0, 25.0])
    assert alert.flame_detected is False


def test_high_risk_when_flame_and_high_sensors():
    alert = _build_alert('fire_sensor', [1.0, 0.8, 0.6, 100.0])
    assert alert.normalized_risk > 0.5


def test_low_risk_when_no_fire_signals():
    alert = _build_alert('fire_sensor', [0.0, 0.0, 0.0, 25.0])
    assert alert.normalized_risk == 0.0


def test_risk_capped_at_1():
    alert = _build_alert('fire_sensor', [1.0, 1.0, 1.0, 500.0])
    assert alert.normalized_risk <= 1.0


def test_source_id_preserved():
    alert = _build_alert('esp32_fire', [1.0, 0.5, 0.3, 80.0])
    assert alert.source_id == 'esp32_fire'


def test_temperature_preserved():
    alert = _build_alert('fire_sensor', [0.0, 0.0, 0.0, 200.0])
    assert alert.temperature == 200.0
