def namespaced(robot_id, topic):
    return f'/{robot_id}/{topic.lstrip("/")}'
