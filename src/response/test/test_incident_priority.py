from response.incident_manager import prioritize_incidents


def test_incident_priority_orders_fire_before_rescue():
    ordered = prioritize_incidents([
        {'type': 'rescue', 'priority': 70},
        {'type': 'fire', 'priority': 100},
    ])
    assert ordered[0]['type'] == 'fire'

