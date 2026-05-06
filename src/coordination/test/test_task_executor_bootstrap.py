import pytest
pytest.importorskip('geometry_msgs.msg')
pytest.importorskip('rclpy')

import rclpy
from geometry_msgs.msg import Pose

from coordination.task_executor_node import TaskExecutorNode


def test_task_executor_uses_identity_goal_before_slam_tf():
    rclpy.init()
    node = TaskExecutorNode(parameter_overrides=[
        rclpy.parameter.Parameter('tf_listener_spin_thread', rclpy.Parameter.Type.BOOL, False),
    ])

    try:
        target = Pose()
        target.position.x = 1.25
        target.position.y = -0.5
        target.orientation.w = 1.0

        goal = node._transform_goal_to_odom('robot1', target)

        assert goal is not None
        assert goal.position.x == pytest.approx(1.25)
        assert goal.position.y == pytest.approx(-0.5)
        assert goal.orientation.w == pytest.approx(1.0)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
