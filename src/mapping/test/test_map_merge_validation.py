import pytest
pytest.importorskip('nav_msgs.msg')
import math

from nav_msgs.msg import OccupancyGrid

from mapping.map_merge_node import MapMergeNode


def test_map_merge_rejects_empty_initial_maps():
    msg = OccupancyGrid()
    msg.info.width = 0
    msg.info.height = 0
    msg.info.resolution = 0.05

    assert not MapMergeNode._is_valid_map(msg)


def test_map_merge_accepts_nonempty_maps():
    msg = OccupancyGrid()
    msg.info.width = 2
    msg.info.height = 2
    msg.info.resolution = 0.05
    msg.data = [0, -1, 50, 100]

    assert MapMergeNode._is_valid_map(msg)


def test_map_merge_projects_points_through_translation_and_rotation():
    x, y = MapMergeNode._transform_xy(1.0, 0.0, (2.0, 3.0, math.pi / 2.0))

    assert x == pytest.approx(2.0)
    assert y == pytest.approx(4.0)
