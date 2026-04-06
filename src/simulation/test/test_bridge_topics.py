from pathlib import Path


def test_bridge_topics_config_and_launch_contract():
    cfg_file = Path(__file__).resolve().parents[1] / 'config' / 'bridge_topics_robot.yaml'
    launch_file = Path(__file__).resolve().parents[1] / 'launch' / 'bridge_robot.launch.py'

    cfg_text = cfg_file.read_text(encoding='utf-8')
    launch_text = launch_file.read_text(encoding='utf-8')

    assert 'scan' in cfg_text
    assert 'odom' in cfg_text
    assert 'camera' in cfg_text
    assert 'ros_gz_bridge' in launch_text
    assert 'parameter_bridge' in launch_text

