import os
import shutil
import time
from pathlib import Path

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.actions import OpaqueFunction
from launch.actions import TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.logging import get_logger
from launch.substitutions import PathJoinSubstitution
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    logger = get_logger('launch.user')
    simulation = LaunchConfiguration('simulation')
    use_sim_time = LaunchConfiguration('use_sim_time')
    world_name = LaunchConfiguration('world_name')
    start_paused = LaunchConfiguration('start_paused')
    rviz_config = LaunchConfiguration('rviz_config')
    rviz_config_out = LaunchConfiguration('rviz_config_out')

    def _prepare_rviz_config(context, *args, **kwargs):
        source = rviz_config.perform(context)
        target = rviz_config_out.perform(context)
        if target == '/tmp/firescout_viz_runtime.rviz':
            target = f"/tmp/firescout_viz_runtime_{int(time.time())}.rviz"
            context.launch_configurations['rviz_config_out'] = target
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy(source, target)
        fixed_frame = _read_rviz_global_fixed_frame(Path(target))
        if fixed_frame == 'unknown':
            logger.warning(
                'RViz config does not define Visualization Manager -> '
                'Global Options -> Fixed Frame; RViz may fall back to its default.'
            )
        logger.info(f"RViz config copied to {target} (Global Options Fixed Frame: {fixed_frame})")
        return []

    def _read_rviz_global_fixed_frame(path: Path) -> str:
        """Read the Fixed Frame exactly where RViz2 expects it in the config."""
        in_visualization_manager = False
        in_global_options = False
        try:
            with path.open('r', encoding='utf-8') as handle:
                for line in handle:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    indent = len(line) - len(line.lstrip(' '))

                    if indent == 0:
                        in_visualization_manager = stripped == 'Visualization Manager:'
                        in_global_options = False
                        continue

                    if not in_visualization_manager:
                        continue

                    if indent == 2:
                        in_global_options = stripped == 'Global Options:'
                        continue

                    if in_global_options and indent == 4 and stripped.startswith('Fixed Frame:'):
                        return stripped.split(':', 1)[1].strip()
        except OSError as exc:
            logger.warning(f"RViz config read failed: {exc}")
        return 'unknown'

    simulation_arg = DeclareLaunchArgument(
        'simulation',
        default_value='true',
        description='Run simulation stack when true.',
    )
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulated clock.',
    )
    world_name_arg = DeclareLaunchArgument(
        'world_name',
        default_value='villa_world',
        description='Gazebo world name used by spawn/bridge nodes.',
    )
    start_paused_arg = DeclareLaunchArgument(
        'start_paused',
        default_value='false',
        description='Start Gazebo paused. Use false for live sensor streams.',
    )
    rviz_config_arg = DeclareLaunchArgument(
        'rviz_config',
        default_value=PathJoinSubstitution([
            FindPackageShare('bringup'), 'config', 'firescout_viz.rviz'
        ]),
        description='Source RViz config that will be copied on launch.',
    )
    rviz_config_out_arg = DeclareLaunchArgument(
        'rviz_config_out',
        default_value='/tmp/firescout_viz_runtime.rviz',
        description='Runtime RViz config path to ensure clean settings each launch.',
    )
    global_stack = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('bringup'),
                'launch',
                'global_stack.launch.py',
            ])
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'simulation': simulation,
            'world_name': world_name,
        }.items(),
    )

    simulation_world = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('simulation'),
                'launch',
                'sim.launch.py',
            ])
        ),
        condition=IfCondition(simulation),
        launch_arguments={
            'start_paused': start_paused,
        }.items(),
    )

    robot_groups = []
    robot_specs = (
        ('robot1', '-2.0', '-2.0'),
        ('robot2', '0.0', '-2.0'),
        ('robot3', '2.0', '-2.0'),
    )
    for index, (robot_id, spawn_x, spawn_y) in enumerate(robot_specs):
        robot_stack = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('bringup'),
                    'launch',
                    'robot_stack.launch.py',
                ])
            ),
            launch_arguments={
                'simulation': simulation,
                'robot_id': robot_id,
                'spawn_x': spawn_x,
                'spawn_y': spawn_y,
                'use_sim_time': use_sim_time,
                'world_name': world_name,
            }.items(),
        )
        robot_groups.append(
            TimerAction(
                period=12.0 + 4.0 * index,
                actions=[robot_stack],
            )
        )

    rviz_node = TimerAction(
        period=26.0,   # last robot spawns at 12+4*2=20 s; allow extra margin
        actions=[Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}],
            arguments=['-d', rviz_config_out],
        )],
    )

    return LaunchDescription([
        simulation_arg,
        use_sim_time_arg,
        world_name_arg,
        start_paused_arg,
        rviz_config_arg,
        rviz_config_out_arg,
        simulation_world,
        global_stack,
        *robot_groups,
        OpaqueFunction(function=_prepare_rviz_config),
        rviz_node,
    ])
