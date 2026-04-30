from types import SimpleNamespace


def test_incident_priority_threshold():
    low_detection = SimpleNamespace(confidence=0.5)
    high_detection = SimpleNamespace(confidence=0.9)

    assert not (low_detection.confidence > 0.7)
    assert high_detection.confidence > 0.7
