from exploration.frontier_logic import FrontierCandidate, select_frontiers


def test_frontier_output_filters_and_orders_frontiers():
    frontiers = [
        FrontierCandidate('f1', 'robot1', area_m2=1.0, info_gain=8.0, travel_cost=3.0, reachable=True),
        FrontierCandidate('f2', 'robot1', area_m2=0.2, info_gain=10.0, travel_cost=1.0, reachable=True),
        FrontierCandidate('f3', 'robot1', area_m2=1.2, info_gain=8.0, travel_cost=2.0, reachable=True),
        FrontierCandidate('f4', 'robot1', area_m2=1.1, info_gain=4.0, travel_cost=12.0, reachable=True),
        FrontierCandidate('f5', 'robot1', area_m2=1.1, info_gain=9.0, travel_cost=2.5, reachable=False),
    ]

    ranked = select_frontiers(frontiers, min_size=0.5, max_travel_cost=10.0)

    assert [frontier.frontier_id for frontier in ranked] == ['f3', 'f1']
