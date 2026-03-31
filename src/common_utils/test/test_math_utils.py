from common_utils.math_utils import clamp


def test_clamp_range():
    assert clamp(10, 0, 5) == 5
