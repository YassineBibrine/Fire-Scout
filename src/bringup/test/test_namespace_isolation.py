import importlib.util
from pathlib import Path
from typing import Any, cast

from launch_ros.actions import PushRosNamespace


def _collect_push_namespaces(entities):
    pushes = []
    for entity in entities:
        if isinstance(entity, PushRosNamespace):
            pushes.append(entity)
        sub_entities = []
        if hasattr(entity, 'get_sub_entities'):
            try:
                sub_entities.extend(entity.get_sub_entities())
            except Exception:
                sub_entities = sub_entities
        actions = getattr(entity, 'actions', None)
        if actions:
            sub_entities.extend(actions)
        if sub_entities:
            pushes.extend(_collect_push_namespaces(sub_entities))
    return pushes


def _namespace_text(push_action: PushRosNamespace) -> str:
    parts = []
    for substitution in push_action.namespace:
        sub_any = cast(Any, substitution)
        text_value = getattr(sub_any, 'text', None)
        if text_value is not None:
            parts.append(str(text_value))
            continue
        name_value = getattr(sub_any, 'name', None)
        if name_value is not None:
            parts.append(str(name_value))
            continue
        parts.append(str(sub_any))
    return ''.join(parts)


def _load_launch_module(path: Path):
    module_name = f"_launch_{path.name.replace('.', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_namespace_isolation_pushes_robot_namespaces():
    launch_path = Path(__file__).resolve().parents[1] / 'launch' / 'full_system.launch.py'
    module = _load_launch_module(launch_path)
    description = module.generate_launch_description()

    push_actions = _collect_push_namespaces(description.entities)
    namespaces = {_namespace_text(action) for action in push_actions}

    for robot_id in ('robot1', 'robot2', 'robot3'):
        assert robot_id in namespaces
