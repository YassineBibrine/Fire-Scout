import importlib.util
from pathlib import Path

from launch.actions import IncludeLaunchDescription


def _collect_includes(entities):
    includes = []
    for entity in entities:
        if isinstance(entity, IncludeLaunchDescription):
            includes.append(entity)
        sub_entities = []
        if hasattr(entity, 'get_sub_entities'):
            try:
                sub_entities.extend(entity.get_sub_entities())
            except Exception:
                pass
        actions = getattr(entity, 'actions', None)
        if actions:
            sub_entities.extend(actions)
        if sub_entities:
            includes.extend(_collect_includes(sub_entities))
    return includes


def _load_launch_module(path: Path):
    module_name = f"_launch_{path.name.replace('.', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_full_system_passes_robot_ids_to_robot_stack_includes():
    launch_path = Path(__file__).resolve().parents[1] / 'launch' / 'full_system.launch.py'
    module = _load_launch_module(launch_path)
    description = module.generate_launch_description()

    robot_ids = set()
    for include in _collect_includes(description.entities):
        launch_arguments = dict(getattr(include, 'launch_arguments', []) or [])
        robot_id = launch_arguments.get('robot_id')
        if robot_id is not None:
            robot_ids.add(str(robot_id))

    assert {'robot1', 'robot2', 'robot3'} <= robot_ids
