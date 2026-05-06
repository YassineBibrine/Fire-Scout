from pathlib import Path


def test_frontier_detector_waits_for_odom_before_bootstrap():
    source = Path(__file__).resolve().parents[1] / 'exploration' / 'frontier_detector_node.py'
    text = source.read_text(encoding='utf-8')

    assert "f'/{self.robot_id}/odom'" in text
    assert 'self._odom_seen = False' in text
    assert 'if not self._odom_seen:' in text
    assert 'return []' in text
