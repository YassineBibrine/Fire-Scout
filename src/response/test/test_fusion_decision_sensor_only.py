"""
Tests verifying sensor-only fusion behavior when camera data is absent
or below threshold.
"""

_SENSOR_THRESHOLD = 0.5
_VISION_THRESHOLD = 0.4


def _sensor_fire(
    flame_detected: bool,
    normalized_risk: float,
) -> bool:
    return flame_detected or normalized_risk >= _SENSOR_THRESHOLD


def _vision_fire(fire_vision_confidence: float) -> bool:
    return fire_vision_confidence >= _VISION_THRESHOLD


def _fire_confirmed(
    flame_detected: bool,
    normalized_risk: float,
    fire_vision_confidence: float,
) -> bool:
    sensor = _sensor_fire(flame_detected, normalized_risk)
    vision = _vision_fire(fire_vision_confidence)
    return sensor and vision


def _sensor_confidence(normalized_risk: float) -> float:
    return float(normalized_risk)


def _risk(sensor_conf: float, vision_conf: float, confirmed: bool) -> float:
    if confirmed:
        return (sensor_conf + vision_conf) / 2.0
    return 0.0


def _action(fire_confirmed: bool, human_confirmed: bool) -> str:
    if human_confirmed:
        return 'RESCUE'
    if fire_confirmed:
        return 'SUPPRESS'
    return 'NONE'


# ---------------------------------------------------------------------------
# Fire NOT confirmed when sensor triggers but camera data is absent / below threshold
# ---------------------------------------------------------------------------


def test_fire_not_confirmed_when_sensor_triggers_but_no_camera_detection():
    """Sensor fires (flame detected, high risk) but no camera detection.
    Expected: fire NOT confirmed because 2-of-2 requires both sensor AND vision."""
    assert _fire_confirmed(
        flame_detected=True,
        normalized_risk=0.9,
        fire_vision_confidence=0.0,
    ) is False


def test_fire_not_confirmed_when_vision_below_threshold():
    """Sensor fires but camera confidence is below vision threshold.
    Expected: fire NOT confirmed."""
    assert _fire_confirmed(
        flame_detected=True,
        normalized_risk=0.8,
        fire_vision_confidence=0.3,
    ) is False


def test_fire_not_confirmed_when_sensor_below_threshold_and_no_camera():
    """Sensor risk below threshold and no camera detection.
    Expected: fire NOT confirmed."""
    assert _fire_confirmed(
        flame_detected=False,
        normalized_risk=0.3,
        fire_vision_confidence=0.0,
    ) is False


# ---------------------------------------------------------------------------
# Risk is zero when neither source confirms
# ---------------------------------------------------------------------------


def test_risk_is_zero_when_neither_source_confirms():
    """No fire confirmation → risk is 0."""
    confirmed = _fire_confirmed(
        flame_detected=False,
        normalized_risk=0.3,
        fire_vision_confidence=0.0,
    )
    r = _risk(
        sensor_conf=_sensor_confidence(0.3),
        vision_conf=0.0,
        confirmed=confirmed,
    )
    assert r == 0.0


def test_risk_is_zero_when_only_sensor_triggers_without_vision():
    """Sensor alone (no vision) → fire not confirmed → risk 0."""
    confirmed = _fire_confirmed(
        flame_detected=True,
        normalized_risk=0.8,
        fire_vision_confidence=0.0,
    )
    r = _risk(
        sensor_conf=_sensor_confidence(0.8),
        vision_conf=0.0,
        confirmed=confirmed,
    )
    assert r == 0.0


# ---------------------------------------------------------------------------
# Sensor-only alert produces preliminary incident (sensor confidence > 0)
# ---------------------------------------------------------------------------


def test_sensor_only_alert_produces_preliminary_incident():
    """Sensor fires alone → sensor_confidence > 0 even though fire isn't
    fully confirmed (2-of-2 not met without vision)."""
    conf = _sensor_confidence(0.8)
    assert conf > 0.0
    confirmed = _fire_confirmed(
        flame_detected=True,
        normalized_risk=0.8,
        fire_vision_confidence=0.0,
    )
    assert confirmed is False


# ---------------------------------------------------------------------------
# Action is NONE when fire not confirmed and no human detected
# ---------------------------------------------------------------------------


def test_action_none_when_sensor_only():
    """Only sensor fires, no vision → action NONE."""
    assert _action(fire_confirmed=False, human_confirmed=False) == 'NONE'


def test_action_none_when_neither_sensor_nor_vision():
    """Neither sensor nor vision → action NONE."""
    assert _action(fire_confirmed=False, human_confirmed=False) == 'NONE'
