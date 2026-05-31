from pathlib import Path


RESPONSE_DIR = Path(__file__).resolve().parents[1] / 'response'


def _source(filename):
    return (RESPONSE_DIR / filename).read_text(encoding='utf-8')


def test_fusion_publishes_periodic_decisions_for_liveness():
    source = _source('fusion_decision_node.py')

    assert "self.declare_parameter('publish_rate_hz', 2.0)" in source
    assert 'self.create_timer(1.0 / self._publish_rate_hz, self._publish_decision)' in source


def test_fusion_decision_propagates_global_incident_position():
    source = _source('fusion_decision_node.py')

    assert 'decision.incident_position = incident_position' in source
    assert "lookup_transform(\n                'map'," in source


def test_detection_nodes_preserve_fusion_incident_position():
    assert 'detection.position = msg.incident_position' in _source('fire_detection_node.py')
    assert 'detection.position = msg.incident_position' in _source('human_detection_node.py')


def test_robot_inference_requires_model_unless_debug_stub_is_explicit():
    source = _source('camera_inference_node.py')

    assert "self.declare_parameter('allow_stub_inference', False)" in source
    assert "import_module('ultralytics')" in source
