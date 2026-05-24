from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
    SetEnvironmentVariable,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    start_paused = LaunchConfiguration('start_paused')
    spawn_fire_entities = LaunchConfiguration('spawn_fire_entities')
    spawn_human_entities = LaunchConfiguration('spawn_human_entities')

    pkg_sim = get_package_share_directory('simulation')

    # Use the provided world file `world_1.sdf` from the simulation/worlds dir.
    world = os.path.join(pkg_sim, 'worlds', 'world_1.sdf')

    # 🔥 IMPORTANT : Tell Gazebo where to find resources (meshes, models, etc)
    ros_share_dir = os.path.dirname(pkg_sim)  # Get /opt/ros/kilted/share/

    # Set GZ_SIM_RESOURCE_PATH for simulation resources
    gz_resource_path = f'{pkg_sim}{os.pathsep}{ros_share_dir}'
    set_gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=gz_resource_path
    )

    # Set GZ_MODEL_PATH for model/mesh resolution
    set_gz_model_path = SetEnvironmentVariable(
        name='GZ_MODEL_PATH',
        value=f'{pkg_sim}{os.pathsep}{ros_share_dir}'
    )

    # Disable FastDDS shared memory transport for this launch to reduce port-lock spam.
    set_fastrtps_shm = SetEnvironmentVariable(
        name='FASTDDS_BUILTIN_TRANSPORTS',
        value='UDPv4'
    )

    start_paused_arg = DeclareLaunchArgument(
        'start_paused',
        default_value='false',
        description='Open Gazebo paused so models and bridges settle before physics runs.',
    )

    # Phase 2: fire and human scenario entity toggles.
    # Set to 'false' for CI runs that do not need scenario entities.
    spawn_fire_entities_arg = DeclareLaunchArgument(
        'spawn_fire_entities',
        default_value='true',
        description=(
            'Spawn fire scenario entities in the world (fire_entity). '
            'Set false to disable for lightweight CI runs.'
        ),
    )
    spawn_human_entities_arg = DeclareLaunchArgument(
        'spawn_human_entities',
        default_value='true',
        description=(
            'Spawn human scenario entities in the world '
            '(human_victim_1, human_victim_2, human_victim_3_blocked, debris). '
            'Set false to disable for lightweight CI runs.'
        ),
    )

    def _gazebo_args(context):
        paused = start_paused.perform(context).lower() in ('true', '1', 'yes')
        fire_on = spawn_fire_entities.perform(context).lower() not in ('false', '0', 'no')
        human_on = spawn_human_entities.perform(context).lower() not in ('false', '0', 'no')

        run_flag = '' if paused else '-r '

        # When scenario entities are disabled the base world still loads but
        # the fire/human models are hidden via Gazebo's --model-filter arg.
        # Since Gazebo Ionic does not expose a reliable per-model disable flag
        # at launch time we rely on SDF world variants instead.  The simplest
        # approach compatible with Gazebo Ionic is to build a minimal patched
        # world file at runtime that omits the unwanted entity blocks.
        effective_world = _build_effective_world(world, fire_on, human_on)

        return [IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    get_package_share_directory('ros_gz_sim'),
                    'launch',
                    'gz_sim.launch.py'
                )
            ),
            launch_arguments={'gz_args': f"{run_flag}{effective_world}"}.items()
        )]

    return LaunchDescription([
        start_paused_arg,
        spawn_fire_entities_arg,
        spawn_human_entities_arg,
        set_gz_resource_path,
        set_gz_model_path,
        set_fastrtps_shm,
        OpaqueFunction(function=_gazebo_args),
    ])


def _build_effective_world(base_world_path: str, fire_on: bool, human_on: bool) -> str:
    """Return the world file path to pass to Gazebo.

    When both scenario flags are True the base world is used unchanged.
    When one or both flags are False a stripped-down world is generated in
    /tmp so Gazebo does not load the disabled entities — useful for CI.

    The generated file is deterministic for the same flag combination so
    repeated launches with the same flags reuse the same /tmp file.
    """
    if fire_on and human_on:
        # No modifications needed; use the installed world as-is.
        return base_world_path

    import re

    suffix = f"fire{int(fire_on)}_human{int(human_on)}"
    tmp_path = f"/tmp/firescout_world_{suffix}.sdf"

    try:
        with open(base_world_path, 'r', encoding='utf-8') as fh:
            content = fh.read()
    except OSError:
        # Fallback: return base world and let Gazebo handle it.
        return base_world_path

    # Entity name patterns to strip when the scenario is disabled.
    # These correspond exactly to the model names in world_1.sdf.
    fire_model_names = ['fire_entity']
    human_model_names = [
        'human_victim_1', 'human_victim_2', 'human_victim_3_blocked',
        'debris_left', 'debris_right',
    ]

    models_to_remove = []
    if not fire_on:
        models_to_remove.extend(fire_model_names)
    if not human_on:
        models_to_remove.extend(human_model_names)

    for model_name in models_to_remove:
        # Remove the entire <model name="..."> ... </model> block.
        pattern = (
            r'<model\s+name=["\']' + re.escape(model_name) + r'["\']'
            r'.*?</model>'
        )
        content = re.sub(pattern, '', content, flags=re.DOTALL)

    with open(tmp_path, 'w', encoding='utf-8') as fh:
        fh.write(content)

    return tmp_path