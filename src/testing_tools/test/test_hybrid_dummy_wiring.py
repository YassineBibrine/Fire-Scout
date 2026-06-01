from pathlib import Path


TESTING_TOOLS_DIR = Path(__file__).resolve().parents[1]


def test_mock_camera_inference_is_scoped_to_one_robot_id():
    source = (
        TESTING_TOOLS_DIR / 'testing_tools' / 'mock_camera_inference_node.py'
    ).read_text(encoding='utf-8')

    assert "self.declare_parameter('robot_id', 'robot1')" in source
    assert "self._robot_ids = [robot_id] if robot_id else ['robot1']" in source


def test_dummy_robot_stack_launches_esp32_sensor_publisher():
    source = (
        TESTING_TOOLS_DIR / 'launch' / 'robot_dummy_stack.launch.py'
    ).read_text(encoding='utf-8')

    assert "executable='dummy_esp32_sensor_pub'" in source
