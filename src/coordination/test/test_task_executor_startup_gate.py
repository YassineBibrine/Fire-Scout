from pathlib import Path


def test_task_executor_does_not_publish_cmd_vel_without_odom():
    source = Path(__file__).resolve().parents[1] / 'coordination' / 'task_executor_node.py'
    text = source.read_text(encoding='utf-8')

    assert 'if odom is None:' in text
    odom_guard = text.index('if odom is None:')
    next_continue = text.index('continue', odom_guard)
    next_publish = text.index('self._cmd_vel_publishers[robot_id].publish(twist)', odom_guard)

    assert next_continue < next_publish


def test_task_executor_has_priority_guard():
    source = Path(__file__).resolve().parents[1] / 'coordination' / 'task_executor_node.py'
    text = source.read_text(encoding='utf-8')

    assert '_task_priority' in text
