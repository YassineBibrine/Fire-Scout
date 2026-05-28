from common_utils import weighted_confidence
from pytest import approx


def test_weighted_confidence_uses_default_sensor_and_vision_weights():
    assert weighted_confidence(0.9, 0.3) == approx(0.66)


def test_weighted_confidence_normalizes_custom_weights():
    assert weighted_confidence(1.0, 0.0, sensor_weight=2.0, vision_weight=1.0) == approx(2.0 / 3.0)


def test_weighted_confidence_clamps_confidences_and_ignores_negative_weights():
    assert weighted_confidence(2.0, 0.5, sensor_weight=-1.0, vision_weight=1.0) == 0.5
    assert weighted_confidence(0.8, 0.8, sensor_weight=0.0, vision_weight=0.0) == 0.0
