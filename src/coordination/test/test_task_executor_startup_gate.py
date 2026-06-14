from pathlib import Path


def test_task_executor_uses_direct_cmd_vel_publishers():
    source = Path(__file__).resolve().parents[1] / 'coordination' / 'task_executor_node.py'
    text = source.read_text(encoding='utf-8')

    assert 'NavigateToPose' not in text
    assert 'ActionClient' not in text
    assert 'nav2_msgs' not in text
    assert 'cmd_vel' in text
    assert 'Twist' in text


def test_task_executor_has_priority_guard():
    source = Path(__file__).resolve().parents[1] / 'coordination' / 'task_executor_node.py'
    text = source.read_text(encoding='utf-8')

    assert '_task_priority' in text
