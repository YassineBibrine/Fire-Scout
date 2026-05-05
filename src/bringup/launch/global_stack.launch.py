from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulated clock.',
    )

    includes = [
        Node(
            package='mapping',
            executable='lidar_demux_node',
            name='lidar_demux_node',
            output='screen',
            parameters=[
                {'use_sim_time': use_sim_time},
                {'robot_ids': ['robot1', 'robot2', 'robot3']},
                {'input_topic': '/lidar'},
            ],
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
    ]

    return LaunchDescription([
        use_sim_time_arg,
        *includes,
    ])
