from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    simulation = LaunchConfiguration('simulation')
    robot_id = LaunchConfiguration('robot_id')
    spawn_x = LaunchConfiguration('spawn_x')
    spawn_y = LaunchConfiguration('spawn_y')
    use_sim_time = LaunchConfiguration('use_sim_time')

    simulation_arg = DeclareLaunchArgument(
        'simulation',
        default_value='true',
        description='Run simulation-specific nodes when true.',
    )
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

    includes = [
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('simulation'),
                    'launch',
                    'spawn_robot.launch.py',
                ])
            ),
            condition=IfCondition(simulation),
            launch_arguments={
                'robot_id': robot_id,
                'spawn_x': spawn_x,
                'spawn_y': spawn_y,
                'use_sim_time': use_sim_time,
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('simulation'),
                    'launch',
                    'bridge_robot.launch.py',
                ])
            ),
            condition=IfCondition(simulation),
            launch_arguments={
                'robot_id': robot_id,
                'use_sim_time': use_sim_time,
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('mapping'),
                    'launch',
                    'slam_robot.launch.py',
                ])
            ),
            launch_arguments={
                'robot_id': robot_id,
                'use_sim_time': use_sim_time,
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('exploration'),
                    'launch',
                    'frontier_robot.launch.py',
                ])
            ),
            launch_arguments={
                'robot_id': robot_id,
                'use_sim_time': use_sim_time,
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('response'),
                    'launch',
                    'detection_robot.launch.py',
                ])
            ),
            launch_arguments={
                'robot_id': robot_id,
                'use_sim_time': use_sim_time,
            }.items(),
        ),
    ]

    return LaunchDescription([
        simulation_arg,
        robot_id_arg,
        spawn_x_arg,
        spawn_y_arg,
        use_sim_time_arg,
        *includes,
    ])
