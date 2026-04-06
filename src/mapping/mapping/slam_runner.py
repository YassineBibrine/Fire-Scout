"""SLAM topic helpers for multi-robot namespace validation."""


def expected_slam_topics(robot_ids):
    return [f'/{robot_id}/map' for robot_id in robot_ids]
