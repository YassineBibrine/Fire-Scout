from exploration.frontier_detector import extract_frontiers


def test_frontier_output_extracts_unknown_adjacent_to_free():
    grid = [
        [100, 100, 100],
        [100, 0, -1],
        [100, -1, -1],
    ]
    frontiers = extract_frontiers(grid)
    assert (1, 2) in frontiers
    assert (2, 1) in frontiers

