from pathlib import Path
from importlib import import_module
from typing import Any, cast


_yaml = cast(Any, import_module('yaml'))


def test_slam_robot_launch_declares_camera_static_tf():
    launch_path = Path(__file__).resolve().parents[1] / 'launch' / 'slam_robot.launch.py'
    source = launch_path.read_text(encoding='utf-8')

    assert 'base_link_to_camera' in source
    assert "'0.10'" in source
    assert "'0.15'" in source
    assert "PathJoinSubstitution([robot_id, 'base_link'])" in source
    assert "PathJoinSubstitution([robot_id, 'camera'])" in source


def test_tf_policy_documents_camera_frame_for_all_robots():
    policy_path = Path(__file__).resolve().parents[1] / 'config' / 'tf_policy.yaml'
    policy = _yaml.safe_load(policy_path.read_text(encoding='utf-8'))

    robots = policy['tf_policy']['robots']
    for robot in robots:
        robot_id = robot['robot_id']
        camera_links = [
            link for link in robot['chain']
            if link.get('child') == f'{robot_id}/camera'
        ]
        assert camera_links, f'{robot_id}/camera missing from tf_policy.yaml'
        camera = camera_links[0]
        assert camera['parent'] == f'{robot_id}/base_link'
        assert camera['published_by'] == 'tf2_ros/static_transform_publisher'
        assert camera['update_rate_hz'] == 'static'
        assert camera['translation_xyz'] == [0.10, 0.0, 0.15]
        assert camera['rotation_rpy'] == [0.0, 0.0, 0.0]
