from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    simulation = LaunchConfiguration('simulation')
    use_sim_time = LaunchConfiguration('use_sim_time')
    world_name = LaunchConfiguration('world_name')

    simulation_arg = DeclareLaunchArgument(
        'simulation',
        default_value='true',
        description='Run simulation-specific nodes when true.',
    )
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulated clock.',
    )
    world_name_arg = DeclareLaunchArgument(
        'world_name',
        default_value='villa_world',
        description='Gazebo world name used by global bridges.',
    )

    includes = [
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('simulation'),
                    'launch',
                    'bridge_global.launch.py',
                ])
            ),
            condition=IfCondition(simulation),
            launch_arguments={'world_name': world_name}.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('mapping'),
                    'launch',
                    'map_merge.launch.py',
                ])
            ),
            launch_arguments={'use_sim_time': use_sim_time}.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('exploration'),
                    'launch',
                    'auction_global.launch.py',
                ])
            ),
            launch_arguments={'use_sim_time': use_sim_time}.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('response'),
                    'launch',
                    'incident_global.launch.py',
                ])
            ),
            launch_arguments={'use_sim_time': use_sim_time}.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('monitoring'),
                    'launch',
                    'monitoring.launch.py',
                ])
            ),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('coordination'),
                    'launch',
                    'coordination_global.launch.py',
                ])
            ),
            launch_arguments={'use_sim_time': use_sim_time}.items(),
        ),
        Node(
            package='coordination',
            executable='coordination_bridge_node',
            name='coordination_bridge_node',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}],
        ),
    ]

    return LaunchDescription([
        simulation_arg,
        use_sim_time_arg,
        world_name_arg,
        *includes,
    ])
