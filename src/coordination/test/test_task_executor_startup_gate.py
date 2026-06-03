from pathlib import Path


def test_task_executor_has_nav2_action_clients():
    source = Path(__file__).resolve().parents[1] / 'coordination' / 'task_executor_node.py'
    text = source.read_text(encoding='utf-8')

    assert 'NavigateToPose' in text
    assert 'ActionClient' in text
    assert 'navigate_to_pose' in text


def test_task_executor_has_priority_guard():
    source = Path(__file__).resolve().parents[1] / 'coordination' / 'task_executor_node.py'
    text = source.read_text(encoding='utf-8')

    assert '_task_priority' in text
