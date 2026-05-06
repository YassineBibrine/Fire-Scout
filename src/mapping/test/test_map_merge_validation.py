import pytest
pytest.importorskip('nav_msgs.msg')

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
