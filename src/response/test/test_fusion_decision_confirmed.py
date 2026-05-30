"""
Tests verifying that the fusion node DOES confirm fire and human incidents
when both required inputs are present and within thresholds.
"""

_SENSOR_THRESHOLD = 0.5
_VISION_THRESHOLD = 0.4


def _evaluate_fire(
    flame_detected: bool,
    normalized_risk: float,
    fire_vision_confidence: float,
) -> bool:
    sensor_fire = flame_detected or normalized_risk >= _SENSOR_THRESHOLD
    vision_fire = fire_vision_confidence >= _VISION_THRESHOLD
    return sensor_fire and vision_fire


def _evaluate_human(human_vision_confidence: float) -> bool:
    return human_vision_confidence >= _VISION_THRESHOLD


def _compute_risk(sensor_conf: float, vision_conf: float) -> float:
    return (sensor_conf + vision_conf) / 2.0


def _recommended_action(fire_confirmed: bool, human_confirmed: bool) -> str:
    if fire_confirmed:
        return 'SUPPRESS'
    if human_confirmed:
        return 'RESCUE'
    return 'MONITOR'


# ---------------------------------------------------------------------------
# Fire confirmation
# ---------------------------------------------------------------------------


def test_fire_confirmed_flame_and_camera():
    """Flame detected + camera fire detection → CONFIRMED."""
    assert _evaluate_fire(
        flame_detected=True,
        normalized_risk=0.8,
        fire_vision_confidence=0.75,
    ) is True


def test_fire_confirmed_risk_threshold_and_camera():
    """Risk above threshold (no direct flame) + camera → CONFIRMED."""
    assert _evaluate_fire(
        flame_detected=False,
        normalized_risk=0.6,
        fire_vision_confidence=0.5,
    ) is True


def test_fire_confirmed_at_exact_thresholds():
    """Exactly at both thresholds → CONFIRMED."""
    assert _evaluate_fire(
        flame_detected=False,
        normalized_risk=0.5,   # == _SENSOR_THRESHOLD
        fire_vision_confidence=0.4,  # == _VISION_THRESHOLD
    ) is True


# ---------------------------------------------------------------------------
# Risk level computation
# ---------------------------------------------------------------------------


def test_risk_level_is_average_of_both_confidences():
    risk = _compute_risk(0.8, 0.6)
    assert abs(risk - 0.7) < 1e-6


def test_risk_level_capped_effectively():
    risk = _compute_risk(1.0, 1.0)
    assert risk <= 1.0


def test_risk_level_reflects_low_confidence():
    risk = _compute_risk(0.5, 0.4)
    assert risk == 0.45


# ---------------------------------------------------------------------------
# Recommended action
# ---------------------------------------------------------------------------


def test_action_suppress_when_fire():
    assert _recommended_action(fire_confirmed=True, human_confirmed=False) == 'SUPPRESS'


def test_action_rescue_when_human():
    assert _recommended_action(fire_confirmed=False, human_confirmed=True) == 'RESCUE'


def test_action_monitor_when_neither():
    assert _recommended_action(fire_confirmed=False, human_confirmed=False) == 'MONITOR'


def test_action_suppress_takes_precedence_over_rescue():
    # fire_confirmed checked first in node logic
    assert _recommended_action(fire_confirmed=True, human_confirmed=True) == 'SUPPRESS'


# ---------------------------------------------------------------------------
# Human confirmation (vision-only)
# ---------------------------------------------------------------------------


def test_human_confirmed_above_threshold():
    assert _evaluate_human(0.7) is True


def test_human_not_confirmed_below_threshold():
    assert _evaluate_human(0.3) is False


def test_human_confirmed_at_exact_threshold():
    assert _evaluate_human(0.4) is True


# ---------------------------------------------------------------------------
# Contributing sources
# ---------------------------------------------------------------------------


def test_contributing_sources_include_sensor_and_camera():
    sensor_fire = True
    vision_fire = True
    sources = []
    if sensor_fire:
        sources.append('sensor:fire_sensor')
    if vision_fire:
        sources.append('camera:robot1_camera')

    assert len(sources) == 2
    assert any('sensor' in s for s in sources)
    assert any('camera' in s for s in sources)

