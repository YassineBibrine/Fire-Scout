from pathlib import Path


def test_spawn_namespaces_config_contains_three_robots():
    cfg_file = Path(__file__).resolve().parents[1] / 'config' / 'robot_spawn_poses.yaml'
    text = cfg_file.read_text(encoding='utf-8')

    assert 'robot1:' in text
    assert 'robot2:' in text
    assert 'robot3:' in text

