import importlib.util
from pathlib import Path


def _load_launch_module(path: Path):
    module_name = f"_launch_{path.name.replace('.', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_spawn_robot_generates_robot_specific_lidar_sdf():
    launch_path = Path(__file__).resolve().parents[1] / 'launch' / 'spawn_robot.launch.py'
    module = _load_launch_module(launch_path)
    source = launch_path.read_text(encoding='utf-8')

    assert module.generate_launch_description().entities
    assert '<topic>/{robot_id_value}/scan</topic>' in source
    assert '<gz_frame_id>{robot_id_value}/lidar</gz_frame_id>' in source
    assert '/tmp' in source
