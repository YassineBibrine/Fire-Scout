from pathlib import Path
import re


TESTING_TOOLS_DIR = Path(__file__).resolve().parents[1]


def test_mock_camera_inference_is_scoped_to_one_robot_id():
    source = (
        TESTING_TOOLS_DIR / 'testing_tools' / 'mock_camera_inference_node.py'
    ).read_text(encoding='utf-8')

    assert "self.declare_parameter('robot_id', 'robot1')" in source
    assert "self._robot_ids = [robot_id] if robot_id else ['robot1']" in source


def test_sim_fire_sources_are_loaded_from_world_sdf_with_fallbacks():
    camera_source = (
        TESTING_TOOLS_DIR / 'testing_tools' / 'mock_camera_inference_node.py'
    ).read_text(encoding='utf-8')
    sensor_source = (
        TESTING_TOOLS_DIR / 'testing_tools' / 'dummy_esp32_sensor_pub.py'
    ).read_text(encoding='utf-8')

    for source in (camera_source, sensor_source):
        assert "get_package_share_directory('simulation')" in source
        assert "world_1.sdf" in source
        assert 'ET.parse(world_path)' in source

    expected_positions = {
        (3.0, 2.0),
        (4.02, 5.7862),
        (6.67, -4.54),
        (-1.8508, -5.17),
        (-7.3638, 0.9669),
        (-8.05, -3.31),
        (7.77, -1.80),
    }

    for source in (camera_source, sensor_source):
        positions = {
            (float(x), float(y))
            for x, y in re.findall(r'\((-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)', source)
        }
        assert expected_positions <= positions


def test_dummy_robot_stack_launches_esp32_sensor_publisher():
    source = (
        TESTING_TOOLS_DIR / 'launch' / 'robot_dummy_stack.launch.py'
    ).read_text(encoding='utf-8')

    assert "executable='dummy_esp32_sensor_pub'" in source
