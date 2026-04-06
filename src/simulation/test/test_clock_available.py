from pathlib import Path


def test_clock_available_contract_present_in_launches():
    world_launch = Path(__file__).resolve().parents[1] / 'launch' / 'gz_world.launch.py'
    bridge_launch = Path(__file__).resolve().parents[1] / 'launch' / 'bridge_robot.launch.py'

    world_text = world_launch.read_text(encoding='utf-8')
    bridge_text = bridge_launch.read_text(encoding='utf-8')

    assert "'gz_args': ['-r ', world]" in world_text
    assert '/clock@rosgraph_msgs/msg/Clock@gz.msgs.Clock' in bridge_text
