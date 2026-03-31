from common_utils.geometry_utils import distance_2d


def test_distance_2d():
    assert distance_2d(0.0, 0.0, 3.0, 4.0) == 5.0
