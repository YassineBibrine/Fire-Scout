from pathlib import Path

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    robot_id = LaunchConfiguration('robot_id')
    spawn_x = LaunchConfiguration('spawn_x')
    spawn_y = LaunchConfiguration('spawn_y')
    use_sim_time = LaunchConfiguration('use_sim_time')
    world_name = LaunchConfiguration('world_name')

    robot_id_arg = DeclareLaunchArgument(
        'robot_id',
        default_value='robot1',
        description='Robot namespace/id.',
    )
    spawn_x_arg = DeclareLaunchArgument(
        'spawn_x',
        default_value='0.0',
        description='Robot spawn X coordinate in Gazebo.',
    )
    spawn_y_arg = DeclareLaunchArgument(
        'spawn_y',
        default_value='0.0',
        description='Robot spawn Y coordinate in Gazebo.',
    )
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulated clock.',
    )
    world_name_arg = DeclareLaunchArgument(
        'world_name',
        default_value='villa_world',
        description='Gazebo world name that hosts the robot models.',
    )

    def _spawn_robot(context, *args, **kwargs):
        robot_id_value = robot_id.perform(context)

        # Use local Fire-Scout diff-drive model with robot-specific sensor
        # topics. Gazebo's expansion of ~/sensor topics varies by context, so
        # make the LaserScan transport path explicit for each spawned robot.
        pkg_sim = get_package_share_directory('simulation')
        source_model = Path(pkg_sim) / 'models' / 'model.sdf'
        model_text = source_model.read_text(encoding='utf-8')
        model_text = model_text.replace(
            '<topic>~/lidar</topic>',
            (
                f'<topic>/{robot_id_value}/scan</topic>\n'
                f'        <gz_frame_id>{robot_id_value}/lidar</gz_frame_id>'
            ),
        )

        generated_dir = Path('/tmp') / 'firescout_models'
        generated_dir.mkdir(parents=True, exist_ok=True)
        generated_model = generated_dir / f'{robot_id_value}.sdf'
        generated_model.write_text(model_text, encoding='utf-8')

        return [
            Node(
                package='ros_gz_sim',
                executable='create',
                name='spawn_entity',
                output='screen',
                arguments=[
                    '-world', world_name,
                    '-name', robot_id,
                    '-file', str(generated_model),
                    '-x', spawn_x,
                    '-y', spawn_y,
                    '-z', '0.1',
                ],
                parameters=[{'use_sim_time': use_sim_time}],
            )
        ]

    return LaunchDescription([
        robot_id_arg,
        spawn_x_arg,
        spawn_y_arg,
        use_sim_time_arg,
        world_name_arg,
        OpaqueFunction(function=_spawn_robot),
    ])
