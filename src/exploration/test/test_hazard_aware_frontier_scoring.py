from pathlib import Path
from types import SimpleNamespace

from exploration.frontier_logic import FrontierCandidate, apply_hazard_weighting, select_frontiers


def test_high_risk_fusion_decision_multiplies_matching_frontier_travel_cost():
    frontiers = [
        FrontierCandidate('safe', 'robot2', area_m2=1.0, info_gain=8.0, travel_cost=2.0),
        FrontierCandidate('hazard', 'robot1', area_m2=1.0, info_gain=8.0, travel_cost=2.0),
    ]

    scored = apply_hazard_weighting(
        frontiers,
        SimpleNamespace(robot_id='robot1', risk_level=0.8),
    )

    assert [frontier.travel_cost for frontier in scored] == [2.0, 6.0]


def test_missing_fusion_decision_keeps_baseline_scoring():
    frontiers = [
        FrontierCandidate('f1', 'robot1', area_m2=1.0, info_gain=8.0, travel_cost=3.0),
        FrontierCandidate('f2', 'robot1', area_m2=1.0, info_gain=8.0, travel_cost=2.0),
    ]

    ranked = select_frontiers(frontiers, min_size=0.5, max_travel_cost=10.0, hazard_decision=None)

    assert [frontier.frontier_id for frontier in ranked] == ['f2', 'f1']
    assert [frontier.travel_cost for frontier in ranked] == [2.0, 3.0]


def test_high_risk_weighting_can_filter_frontiers_by_weighted_cost():
    frontiers = [
        FrontierCandidate('near_hazard', 'robot1', area_m2=1.0, info_gain=10.0, travel_cost=4.0),
        FrontierCandidate('near_clear', 'robot2', area_m2=1.0, info_gain=8.0, travel_cost=7.0),
    ]

    ranked = select_frontiers(
        frontiers,
        min_size=0.5,
        max_travel_cost=10.0,
        hazard_decision=SimpleNamespace(robot_id='robot1', risk_level=0.9),
    )

    assert [frontier.frontier_id for frontier in ranked] == ['near_clear']


def test_frontier_detector_subscribes_to_fusion_decision_not_raw_fire_incidents():
    source = Path(__file__).resolve().parents[1] / 'exploration' / 'frontier_detector_node.py'
    text = source.read_text(encoding='utf-8')

    assert "f'/{self.robot_id}/fusion_decision'" in text
    assert '/incidents/fire' not in text
