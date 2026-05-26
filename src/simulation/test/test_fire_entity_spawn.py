"""Tests for Phase 2 fire entity in the simulation world.

Verifies without a running Gazebo instance:
- fire_entity model exists in world_1.sdf.
- fire_entity is placed at the expected position (3.0, 2.0, 0).
- fire_entity is declared static (no physics interaction).
- Human victim entities exist at their expected positions.
- sim.launch.py exposes spawn_fire_entities and spawn_human_entities arguments.
- _build_effective_world helper correctly strips entities when flags are False.
"""
import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _world_path() -> Path:
    return Path(__file__).resolve().parents[1] / 'worlds' / 'world_1.sdf'


def _load_world_xml() -> ET.Element:
    tree = ET.parse(str(_world_path()))
    return tree.getroot()


def _find_model(root: ET.Element, name: str):
    """Return the first <model name='{name}'> element, or None."""
    for model in root.iter('model'):
        if model.get('name') == name:
            return model
    return None


def _model_pose(model: ET.Element) -> tuple[float, float, float] | None:
    """Extract (x, y, z) from first <pose> element of model; return None if absent."""
    pose_el = model.find('pose')
    if pose_el is None or not pose_el.text:
        return None
    parts = pose_el.text.strip().split()
    if len(parts) < 3:
        return None
    return float(parts[0]), float(parts[1]), float(parts[2])


def _load_sim_launch_module():
    launch_path = Path(__file__).resolve().parents[1] / 'launch' / 'sim.launch.py'
    spec = importlib.util.spec_from_file_location('_sim_launch', str(launch_path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Fire entity tests
# ---------------------------------------------------------------------------

def test_fire_entity_exists_in_world_sdf():
    """Verify fire_entity model is defined in world_1.sdf."""
    root = _load_world_xml()
    fire = _find_model(root, 'fire_entity')
    assert fire is not None, (
        'fire_entity model not found in world_1.sdf; '
        'Phase 2 fire scenario requires this entity.'
    )


def test_fire_entity_at_correct_position():
    """Verify fire_entity is placed at (3.0, 2.0, 0.0) ± 0.05 m."""
    root = _load_world_xml()
    fire = _find_model(root, 'fire_entity')
    assert fire is not None, 'fire_entity model missing from world_1.sdf'

    pose = _model_pose(fire)
    assert pose is not None, 'fire_entity has no <pose> element'

    x, y, z = pose
    assert abs(x - 3.0) < 0.05, f'fire_entity x={x:.3f} expected ~3.0'
    assert abs(y - 2.0) < 0.05, f'fire_entity y={y:.3f} expected ~2.0'
    assert abs(z - 0.0) < 0.05, f'fire_entity z={z:.3f} expected ~0.0'


def test_fire_entity_is_static():
    """Verify fire_entity has <static>true</static> (no physics interaction)."""
    root = _load_world_xml()
    fire = _find_model(root, 'fire_entity')
    assert fire is not None, 'fire_entity model missing from world_1.sdf'

    static_el = fire.find('static')
    assert static_el is not None, 'fire_entity missing <static> element'
    static_text = static_el.text
    assert static_text is not None, 'fire_entity <static> element is empty'
    assert static_text.strip().lower() == 'true', (
        f'fire_entity <static> is "{static_text.strip()}", expected "true"'
    )


def test_fire_entity_has_red_orange_visuals():
    """Verify fire_entity uses red/orange ambient colour (R > 0.7, G < 0.6, B < 0.2)."""
    root = _load_world_xml()
    fire = _find_model(root, 'fire_entity')
    assert fire is not None, 'fire_entity model missing from world_1.sdf'

    # Find at least one ambient colour element under the fire model
    found_orange = False
    for ambient in fire.iter('ambient'):
        if ambient.text:
            parts = ambient.text.strip().split()
            if len(parts) >= 3:
                r, g, b = float(parts[0]), float(parts[1]), float(parts[2])
                if r > 0.7 and g < 0.6 and b < 0.2:
                    found_orange = True
                    break

    assert found_orange, (
        'fire_entity does not appear to have red/orange visual material. '
        'At least one <ambient> element should have R>0.7, G<0.6, B<0.2.'
    )


# ---------------------------------------------------------------------------
# Human entity tests
# ---------------------------------------------------------------------------

def test_human_victim_1_exists_at_correct_position():
    """Verify primary human victim is at (-3.0, 4.0, 0.0)."""
    root = _load_world_xml()
    human = _find_model(root, 'human_victim_1')
    assert human is not None, 'human_victim_1 not found in world_1.sdf'

    pose = _model_pose(human)
    assert pose is not None, 'human_victim_1 has no <pose> element'

    x, y, z = pose
    assert abs(x - (-3.0)) < 0.05, f'human_victim_1 x={x:.3f} expected ~-3.0'
    assert abs(y - 4.0) < 0.05, f'human_victim_1 y={y:.3f} expected ~4.0'


def test_human_victim_2_exists():
    """Verify secondary human victim (bedroom 2 scenario) exists in world."""
    root = _load_world_xml()
    human = _find_model(root, 'human_victim_2')
    assert human is not None, 'human_victim_2 not found in world_1.sdf'


def test_human_victim_3_blocked_with_debris():
    """Verify blocked-path scenario: victim + two debris obstacles exist."""
    root = _load_world_xml()
    assert _find_model(root, 'human_victim_3_blocked') is not None, (
        'human_victim_3_blocked not found in world_1.sdf'
    )
    assert _find_model(root, 'debris_left') is not None, (
        'debris_left not found in world_1.sdf; blocked-path scenario incomplete'
    )
    assert _find_model(root, 'debris_right') is not None, (
        'debris_right not found in world_1.sdf; blocked-path scenario incomplete'
    )


def test_human_entities_are_static():
    """Verify all human entities are static (no physics interaction)."""
    root = _load_world_xml()
    for name in ('human_victim_1', 'human_victim_2', 'human_victim_3_blocked'):
        model = _find_model(root, name)
        assert model is not None, f'{name} not found in world_1.sdf'
        static_el = model.find('static')
        assert static_el is not None, f'{name} missing <static> element'
        static_text = static_el.text
        assert static_text is not None, f'{name} <static> element is empty'
        assert static_text.strip().lower() == 'true', (
            f'{name} <static> is "{static_text.strip()}", expected "true"'
        )


# ---------------------------------------------------------------------------
# Launch argument tests
# ---------------------------------------------------------------------------

def test_sim_launch_has_spawn_fire_entities_arg():
    """Verify sim.launch.py declares spawn_fire_entities launch argument."""
    launch_path = Path(__file__).resolve().parents[1] / 'launch' / 'sim.launch.py'
    source = launch_path.read_text(encoding='utf-8')
    assert 'spawn_fire_entities' in source, (
        'sim.launch.py missing spawn_fire_entities argument (Phase 2 requirement).'
    )


def test_sim_launch_has_spawn_human_entities_arg():
    """Verify sim.launch.py declares spawn_human_entities launch argument."""
    launch_path = Path(__file__).resolve().parents[1] / 'launch' / 'sim.launch.py'
    source = launch_path.read_text(encoding='utf-8')
    assert 'spawn_human_entities' in source, (
        'sim.launch.py missing spawn_human_entities argument (Phase 2 requirement).'
    )


def test_sim_launch_default_values_are_true():
    """Verify both scenario args default to true so full scenarios load by default."""
    launch_path = Path(__file__).resolve().parents[1] / 'launch' / 'sim.launch.py'
    source = launch_path.read_text(encoding='utf-8')

    # Both args must have 'true' as their default value somewhere near the
    # argument declaration.  We check the raw source for the pattern.
    import re
    fire_default = re.search(
        r'spawn_fire_entities.*?default_value.*?["\']true["\']',
        source, re.DOTALL
    )
    human_default = re.search(
        r'spawn_human_entities.*?default_value.*?["\']true["\']',
        source, re.DOTALL
    )
    assert fire_default is not None, (
        "spawn_fire_entities default_value is not 'true' in sim.launch.py"
    )
    assert human_default is not None, (
        "spawn_human_entities default_value is not 'true' in sim.launch.py"
    )


def test_build_effective_world_strips_fire_when_disabled(tmp_path):
    """Verify _build_effective_world removes fire_entity when fire_on=False."""
    # Write a minimal world SDF with both fire and human models.
    world_content = """<?xml version="1.0" ?>
<sdf version="1.9">
<world name="test_world">
  <model name="fire_entity"><static>true</static><pose>3.0 2.0 0 0 0 0</pose></model>
  <model name="human_victim_1"><static>true</static><pose>-3.0 4.0 0 0 0 0</pose></model>
</world>
</sdf>"""
    world_file = tmp_path / 'test_world.sdf'
    world_file.write_text(world_content, encoding='utf-8')

    module = _load_sim_launch_module()

    result_path = module._build_effective_world(str(world_file), fire_on=False, human_on=True)

    result_content = Path(result_path).read_text(encoding='utf-8')
    assert 'fire_entity' not in result_content, (
        '_build_effective_world should remove fire_entity when fire_on=False'
    )
    assert 'human_victim_1' in result_content, (
        '_build_effective_world should keep human_victim_1 when human_on=True'
    )


def test_build_effective_world_strips_humans_when_disabled(tmp_path):
    """Verify _build_effective_world removes human entities when human_on=False."""
    world_content = """<?xml version="1.0" ?>
<sdf version="1.9">
<world name="test_world">
  <model name="fire_entity"><static>true</static><pose>3.0 2.0 0 0 0 0</pose></model>
  <model name="human_victim_1"><static>true</static><pose>-3.0 4.0 0 0 0 0</pose></model>
  <model name="human_victim_2"><static>true</static><pose>-1.5 -3.0 0 0 0 0</pose></model>
  <model name="debris_left"><static>true</static><pose>2.0 -0.7 0 0 0 0</pose></model>
</world>
</sdf>"""
    world_file = tmp_path / 'test_world2.sdf'
    world_file.write_text(world_content, encoding='utf-8')

    module = _load_sim_launch_module()

    result_path = module._build_effective_world(str(world_file), fire_on=True, human_on=False)

    result_content = Path(result_path).read_text(encoding='utf-8')
    assert 'human_victim_1' not in result_content
    assert 'human_victim_2' not in result_content
    assert 'debris_left' not in result_content
    assert 'fire_entity' in result_content, (
        '_build_effective_world should keep fire_entity when fire_on=True'
    )


def test_build_effective_world_returns_base_when_both_on():
    """Verify _build_effective_world returns the base path when both flags are True."""
    module = _load_sim_launch_module()
    base_path = '/some/fake/world.sdf'
    result = module._build_effective_world(base_path, fire_on=True, human_on=True)
    assert result == base_path, (
        '_build_effective_world should return the base world path unchanged '
        'when both fire_on and human_on are True.'
    )
