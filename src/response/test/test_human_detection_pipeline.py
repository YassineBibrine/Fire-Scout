from response.detection_processor import detection_to_incident


def test_human_detection_pipeline_converts_to_rescue_incident():
    incident = detection_to_incident('human', robot_id='robot2', confidence=0.88)
    assert incident['type'] == 'rescue'
    assert incident['priority'] == 70

