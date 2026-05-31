import importlib.util
from pathlib import Path

from launch import LaunchDescription


def _load_launch_module(path: Path):
    module_name = f"_launch_{path.name.replace('.', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_full_launch_smoke():
    launch_path = Path(__file__).resolve().parents[1] / 'launch' / 'full_system.launch.py'
    module = _load_launch_module(launch_path)
    description = module.generate_launch_description()

    assert isinstance(description, LaunchDescription)
    assert description.entities, 'Expected at least one action in LaunchDescription'
