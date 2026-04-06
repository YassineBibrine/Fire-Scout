from pathlib import Path


def test_full_launch_smoke_contains_required_includes():
    launch_file = Path(__file__).resolve().parents[1] / 'launch' / 'full_system.launch.py'
    text = launch_file.read_text(encoding='utf-8')

    assert 'global_stack.launch.py' in text
    assert 'robot_stack.launch.py' in text
    assert "for robot_id in ('robot1', 'robot2', 'robot3')" in text

