from mapping.map_merger import map_merge_status


def test_map_merge_ready_when_multiple_maps_available():
    status = map_merge_status(['/robot1/map', '/robot2/map'])
    assert status['ready'] is True
    assert status['map_count'] == 2

