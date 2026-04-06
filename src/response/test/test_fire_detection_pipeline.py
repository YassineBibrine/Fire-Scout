from response.detection_processor import detection_to_incident


def test_fire_detection_pipeline_converts_to_fire_incident():
    incident = detection_to_incident('fire', robot_id='robot1', confidence=0.92)
    assert incident['type'] == 'fire'
    assert incident['priority'] == 100

