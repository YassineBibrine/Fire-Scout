"""
Tests for the incident conflict-resolution priority model shared by
rescue_planning_node and suppression_planning_node.

Priority rules (descending importance):
  1. Incident type  - HUMAN always outranks FIRE
  2. Confidence     - higher confidence wins within same type
  3. Robot ID       - robot1 > robot2 > robot3 (deterministic tiebreak)

Concrete examples from the spec:
  Human(0.51) > Fire(0.99)
  Human(0.90) > Human(0.80)
  robot1 > robot2 when type and confidence are equal
"""

# ---------------------------------------------------------------------------
# Priority model (mirrors the implementation in both planning nodes)
# ---------------------------------------------------------------------------

_PRIORITY_HUMAN_BASE = 10.0
_PRIORITY_FIRE_BASE = 5.0

_ROBOT_OFFSET = {
    'robot1': 0.003,
    'robot2': 0.002,
    'robot3': 0.001,
}
_DEFAULT_ROBOT_OFFSET = 0.0


def compute_incident_priority(
    incident_type: str, confidence: float, robot_id: str
) -> float:
    if incident_type == 'human':
        base = _PRIORITY_HUMAN_BASE
    elif incident_type == 'fire':
        base = _PRIORITY_FIRE_BASE
    else:
        base = 0.0
    robot_offset = _ROBOT_OFFSET.get(robot_id, _DEFAULT_ROBOT_OFFSET)
    return base + confidence + robot_offset


# ---------------------------------------------------------------------------
# Rule 1: Human > Fire regardless of confidence
# ---------------------------------------------------------------------------


def test_human_beats_fire_spec_example():
    """Spec: Human(0.51) > Fire(0.99)."""
    h = compute_incident_priority('human', 0.51, 'robot1')
    f = compute_incident_priority('fire', 0.99, 'robot1')
    assert h > f, f'Expected human({h:.4f}) > fire({f:.4f})'


def test_human_min_confidence_beats_fire_max():
    """Human at zero confidence still outranks fire at max confidence."""
    h = compute_incident_priority('human', 0.0, 'robot3')
    f = compute_incident_priority('fire', 1.0, 'robot1')
    assert h > f


def test_human_beats_fire_mid_confidences():
    h = compute_incident_priority('human', 0.5, 'robot2')
    f = compute_incident_priority('fire', 0.8, 'robot2')
    assert h > f


# ---------------------------------------------------------------------------
# Rule 2: Higher confidence wins within same type
# ---------------------------------------------------------------------------


def test_human_higher_confidence_wins_spec_example():
    """Spec: Human(0.90) > Human(0.80)."""
    h90 = compute_incident_priority('human', 0.90, 'robot1')
    h80 = compute_incident_priority('human', 0.80, 'robot1')
    assert h90 > h80


def test_fire_higher_confidence_wins():
    f95 = compute_incident_priority('fire', 0.95, 'robot1')
    f50 = compute_incident_priority('fire', 0.50, 'robot1')
    assert f95 > f50


def test_human_confidence_ordering_three_values():
    p_high = compute_incident_priority('human', 0.95, 'robot1')
    p_mid  = compute_incident_priority('human', 0.70, 'robot1')
    p_low  = compute_incident_priority('human', 0.30, 'robot1')
    assert p_high > p_mid > p_low


def test_fire_confidence_ordering_three_values():
    p_high = compute_incident_priority('fire', 0.90, 'robot1')
    p_mid  = compute_incident_priority('fire', 0.75, 'robot1')
    p_low  = compute_incident_priority('fire', 0.50, 'robot1')
    assert p_high > p_mid > p_low


# ---------------------------------------------------------------------------
# Rule 3: Robot-ID tiebreaker (robot1 > robot2 > robot3)
# ---------------------------------------------------------------------------


def test_robot1_beats_robot2_spec_example():
    """Spec: robot1 > robot2 when type and confidence equal."""
    p1 = compute_incident_priority('fire', 0.75, 'robot1')
    p2 = compute_incident_priority('fire', 0.75, 'robot2')
    assert p1 > p2


def test_robot_id_ordering_all_three():
    p1 = compute_incident_priority('human', 0.70, 'robot1')
    p2 = compute_incident_priority('human', 0.70, 'robot2')
    p3 = compute_incident_priority('human', 0.70, 'robot3')
    assert p1 > p2 > p3


def test_robot1_beats_robot3_fire():
    p1 = compute_incident_priority('fire', 0.80, 'robot1')
    p3 = compute_incident_priority('fire', 0.80, 'robot3')
    assert p1 > p3


def test_unknown_robot_gets_zero_offset():
    p_known   = compute_incident_priority('fire', 0.80, 'robot3')
    p_unknown = compute_incident_priority('fire', 0.80, 'robot99')
    assert p_known > p_unknown


# ---------------------------------------------------------------------------
# Priority values are always non-negative
# ---------------------------------------------------------------------------


def test_priority_non_negative_human():
    p = compute_incident_priority('human', 0.0, 'robot3')
    assert p >= 0.0


def test_priority_non_negative_fire():
    p = compute_incident_priority('fire', 0.0, 'robot3')
    assert p >= 0.0


def test_priority_non_negative_unknown_type():
    p = compute_incident_priority('unknown', 0.5, 'robot1')
    assert p >= 0.0


# ---------------------------------------------------------------------------
# Sorting a mixed incident list
# ---------------------------------------------------------------------------


def test_sorted_incident_list():
    """
    Mixed incident list should sort with human first, then fire,
    within each type by confidence, then robot_id.
    """
    incidents = [
        ('fire',  0.99, 'robot1'),
        ('human', 0.51, 'robot1'),
        ('fire',  0.60, 'robot2'),
        ('human', 0.90, 'robot2'),
    ]
    ranked = sorted(
        incidents,
        key=lambda x: compute_incident_priority(x[0], x[1], x[2]),
        reverse=True,
    )

    # First must be a human incident
    assert ranked[0][0] == 'human'
    # Last must be the lowest-confidence fire
    assert ranked[-1][0] == 'fire'
    # Human(0.90) before Human(0.51)
    human_incidents = [i for i in ranked if i[0] == 'human']
    assert human_incidents[0][1] == 0.90
    assert human_incidents[1][1] == 0.51
