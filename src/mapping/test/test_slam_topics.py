from mapping.slam_runner import expected_slam_topics


def test_slam_topics_include_each_robot_namespace():
    topics = expected_slam_topics(['robot1', 'robot2', 'robot3'])
    assert '/robot1/map' in topics
    assert '/robot2/map' in topics
    assert '/robot3/map' in topics

