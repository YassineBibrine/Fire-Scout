"""Detection-to-incident conversion for the response pipeline."""


def detection_to_incident(detection_type, robot_id, confidence):
    incident_type = 'fire' if detection_type == 'fire' else 'rescue'
    priority = 100 if incident_type == 'fire' else 70
    return {
        'type': incident_type,
        'robot_id': robot_id,
        'confidence': confidence,
        'priority': priority,
    }
