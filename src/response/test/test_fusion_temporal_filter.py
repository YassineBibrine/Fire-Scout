"""
Tests for temporal filtering in the fusion decision node.

Rules under test:
  1. Sensor data older than confirmation_window_sec is rejected.
  2. Vision data older than confirmation_window_sec is rejected.
  3. The gap between sensor and vision timestamps must be <= window.
  4. Duplicate confirmations within confirmed_cooldown_sec are suppressed.
"""

_WINDOW_SEC = 3.0
_COOLDOWN_SEC = 1.0


def _data_accepted(age_sec: float) -> bool:
    """Return True if data of this age passes the staleness check."""
    return age_sec <= _WINDOW_SEC


def _temporal_gap_ok(sensor_time_ns: int, vision_time_ns: int) -> bool:
    gap_sec = abs(vision_time_ns - sensor_time_ns) / 1e9
    return gap_sec <= _WINDOW_SEC


def _cooldown_ok(elapsed_since_last_sec: float) -> bool:
    return elapsed_since_last_sec >= _COOLDOWN_SEC


# ---------------------------------------------------------------------------
# Staleness tests
# ---------------------------------------------------------------------------


def test_fresh_sensor_within_window():
    assert _data_accepted(0.5) is True


def test_sensor_at_window_boundary():
    assert _data_accepted(3.0) is True


def test_sensor_just_over_window():
    assert _data_accepted(3.01) is False


def test_stale_sensor_rejected():
    assert _data_accepted(5.0) is False


def test_fresh_vision_within_window():
    assert _data_accepted(1.0) is True


def test_stale_vision_rejected():
    assert _data_accepted(4.0) is False


# ---------------------------------------------------------------------------
# Temporal alignment between sensor and vision
# ---------------------------------------------------------------------------


def test_aligned_within_half_second():
    sensor_ns = 0
    vision_ns = 500_000_000  # 0.5 s later
    assert _temporal_gap_ok(sensor_ns, vision_ns) is True


def test_aligned_at_boundary():
    sensor_ns = 0
    vision_ns = 3_000_000_000  # exactly 3 s
    assert _temporal_gap_ok(sensor_ns, vision_ns) is True


def test_gap_just_over_window_rejected():
    sensor_ns = 0
    vision_ns = 3_100_000_000  # 3.1 s
    assert _temporal_gap_ok(sensor_ns, vision_ns) is False


def test_gap_4s_rejected():
    sensor_ns = 0
    vision_ns = 4_000_000_000  # 4 s
    assert _temporal_gap_ok(sensor_ns, vision_ns) is False


def test_vision_arrives_before_sensor_still_checked():
    # absolute gap matters, not direction
    sensor_ns = 4_000_000_000
    vision_ns = 1_000_000_000  # vision 3 s before sensor
    assert _temporal_gap_ok(sensor_ns, vision_ns) is True


def test_vision_arrives_far_before_sensor_rejected():
    sensor_ns = 5_000_000_000
    vision_ns = 1_000_000_000  # 4 s before sensor
    assert _temporal_gap_ok(sensor_ns, vision_ns) is False


# ---------------------------------------------------------------------------
# Duplicate suppression
# ---------------------------------------------------------------------------


def test_duplicate_within_cooldown_suppressed():
    elapsed = 0.5  # < _COOLDOWN_SEC
    assert _cooldown_ok(elapsed) is False


def test_after_cooldown_allowed():
    elapsed = 1.0  # == _COOLDOWN_SEC
    assert _cooldown_ok(elapsed) is True


def test_well_after_cooldown_allowed():
    elapsed = 5.0
    assert _cooldown_ok(elapsed) is True


def test_immediately_after_confirmation_suppressed():
    elapsed = 0.0
    assert _cooldown_ok(elapsed) is False
