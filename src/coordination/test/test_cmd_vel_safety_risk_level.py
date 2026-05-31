import pytest

pytest.importorskip('geometry_msgs.msg')

from geometry_msgs.msg import Twist

from coordination.cmd_vel_safety_node import (
    FusionDecisionSnapshot,
    apply_risk_speed_limit,
    should_bypass_obstacle_safety,
)


def _command(speed: float) -> Twist:
    msg = Twist()
    msg.linear.x = speed
    return msg


def test_high_risk_caps_linear_speed():
    decision = FusionDecisionSnapshot(risk_level=0.9, recommended_action='MONITOR')
    capped = apply_risk_speed_limit(
        _command(0.5),
        decision,
        risk_threshold=0.8,
        max_linear_speed=0.1,
    )

    assert capped.linear.x == pytest.approx(0.1)


def test_passthrough_allowed_for_critical_actions():
    assert should_bypass_obstacle_safety(
        FusionDecisionSnapshot(risk_level=0.4, recommended_action='SUPPRESS')
    )
    assert should_bypass_obstacle_safety(
        FusionDecisionSnapshot(risk_level=0.4, recommended_action='RESCUE')
    )
    assert not should_bypass_obstacle_safety(
        FusionDecisionSnapshot(risk_level=0.4, recommended_action='MONITOR')
    )
