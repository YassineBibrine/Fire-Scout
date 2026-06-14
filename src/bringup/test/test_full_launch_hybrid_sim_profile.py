import importlib.util
from pathlib import Path

import pytest

launch = pytest.importorskip('launch')
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


def test_full_system_includes_hybrid_pipeline_with_profile():
    launch_path = Path(__file__).resolve().parents[1] / 'launch' / 'full_system.launch.py'
    hybrid_launch_path = (
        Path(__file__).resolve().parents[2]
        / 'response'
        / 'launch'
        / 'hybrid_pipeline.launch.py'
    )
    module = _load_launch_module(launch_path)
    description = module.generate_launch_description()

    assert hybrid_launch_path.exists()

    hybrid_includes = []
    for include in _collect_includes(description.entities):
        source = getattr(include, 'launch_description_source', None)
        location = getattr(source, 'location', '') if source else ''
        if 'hybrid_pipeline.launch.py' in str(location):
            hybrid_includes.append(include)

    assert len(hybrid_includes) >= 3
    for include in hybrid_includes:
        launch_arguments = dict(getattr(include, 'launch_arguments', []) or [])
        assert 'launch_profile' in launch_arguments


def test_full_system_disables_robot_stack_response_to_avoid_duplicate_hybrid_nodes():
    launch_path = Path(__file__).resolve().parents[1] / 'launch' / 'full_system.launch.py'
    module = _load_launch_module(launch_path)
    description = module.generate_launch_description()

    robot_stack_includes = []
    for include in _collect_includes(description.entities):
        source = getattr(include, 'launch_description_source', None)
        location = getattr(source, 'location', '') if source else ''
        if 'robot_stack.launch.py' in str(location):
            robot_stack_includes.append(include)

    assert len(robot_stack_includes) >= 3
    for include in robot_stack_includes:
        launch_arguments = dict(getattr(include, 'launch_arguments', []) or [])
        assert launch_arguments.get('include_response') == 'false'


def test_full_system_passes_nav2_disabled_by_default_to_robot_stacks():
    launch_path = Path(__file__).resolve().parents[1] / 'launch' / 'full_system.launch.py'
    module = _load_launch_module(launch_path)
    description = module.generate_launch_description()

    robot_stack_includes = []
    for include in _collect_includes(description.entities):
        source = getattr(include, 'launch_description_source', None)
        location = getattr(source, 'location', '') if source else ''
        if 'robot_stack.launch.py' in str(location):
            robot_stack_includes.append(include)

    assert len(robot_stack_includes) >= 3
    for include in robot_stack_includes:
        launch_arguments = dict(getattr(include, 'launch_arguments', []) or [])
        assert 'enable_nav2' in launch_arguments


def test_full_system_requires_incident_robot_for_fire_suppression():
    launch_path = Path(__file__).resolve().parents[1] / 'launch' / 'full_system.launch.py'
    source = launch_path.read_text(encoding='utf-8')

    assert "'allow_any_robot_to_suppress': False" in source
    assert "'auto_suppress_on_detection_robot_ids': ['robot1']" in source
    assert "'auto_suppress_on_detection_model_names': ['fire_entity']" in source
    assert "'auto_suppress_when_close_model_names': ['fire_entity']" in source
    assert "'auto_suppress_when_close_radius_m': 5.0" in source
