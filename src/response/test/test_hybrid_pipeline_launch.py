import importlib.util
from pathlib import Path

import pytest

pytest.importorskip('launch')
pytest.importorskip('launch_ros')


def _load_launch_module(path: Path):
    module_name = f"_launch_{path.name.replace('.', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _executables(nodes):
    return [str(getattr(node, 'node_executable', '')) for node in nodes]


def test_hybrid_pipeline_launch_file_is_installed_by_setup_py():
    setup_py = Path(__file__).resolve().parents[1] / 'setup.py'
    text = setup_py.read_text(encoding='utf-8')

    assert 'launch/hybrid_pipeline.launch.py' in text


def test_sim_profile_uses_mock_camera_inference_only():
    launch_path = Path(__file__).resolve().parents[1] / 'launch' / 'hybrid_pipeline.launch.py'
    module = _load_launch_module(launch_path)

    executables = _executables(module._build_hybrid_nodes('robot1', 'true', 'sim'))

    assert 'mock_camera_inference_node' in executables
    assert 'dummy_esp32_sensor_pub' in executables
    assert 'camera_inference_node' not in executables


def test_robot_profile_uses_real_camera_inference_only():
    launch_path = Path(__file__).resolve().parents[1] / 'launch' / 'hybrid_pipeline.launch.py'
    module = _load_launch_module(launch_path)

    executables = _executables(module._build_hybrid_nodes('robot1', 'true', 'robot'))

    assert 'camera_inference_node' in executables
    assert 'mock_camera_inference_node' not in executables


def test_debug_profile_uses_real_camera_inference_only():
    launch_path = Path(__file__).resolve().parents[1] / 'launch' / 'hybrid_pipeline.launch.py'
    module = _load_launch_module(launch_path)

    executables = _executables(module._build_hybrid_nodes('robot1', 'true', 'debug'))

    assert 'camera_inference_node' in executables
    assert 'mock_camera_inference_node' not in executables
