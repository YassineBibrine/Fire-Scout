def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def weighted_confidence(sensor_conf, vision_conf, sensor_weight=0.6, vision_weight=0.4):
    sensor_weight = max(float(sensor_weight), 0.0)
    vision_weight = max(float(vision_weight), 0.0)
    total_weight = sensor_weight + vision_weight
    if total_weight <= 0.0:
        return 0.0

    sensor_conf = clamp(float(sensor_conf), 0.0, 1.0)
    vision_conf = clamp(float(vision_conf), 0.0, 1.0)
    combined = (sensor_conf * sensor_weight + vision_conf * vision_weight) / total_weight
    return clamp(combined, 0.0, 1.0)
