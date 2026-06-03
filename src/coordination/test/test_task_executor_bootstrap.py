import pytest
pytest.importorskip('geometry_msgs.msg')
pytest.importorskip('rclpy')

import rclpy
from rclpy.parameter import Parameter

from coordination.task_executor_node import TaskExecutorNode


def test_task_executor_creates_nav_clients():
    rclpy.init()
    node = TaskExecutorNode(parameter_overrides=[
        Parameter('robot_ids', Parameter.Type.STRING_ARRAY, ['robot1', 'robot2', 'robot3']),
    ])

    try:
        assert 'robot1' in node._nav_clients
        assert 'robot2' in node._nav_clients
        assert 'robot3' in node._nav_clients
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
