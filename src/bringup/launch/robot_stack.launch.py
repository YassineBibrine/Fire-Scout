from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    simulation = LaunchConfiguration('simulation')
    robot_id = LaunchConfiguration('robot_id')
    spawn_x = LaunchConfiguration('spawn_x')
    spawn_y = LaunchConfiguration('spawn_y')
    use_sim_time = LaunchConfiguration('use_sim_time')
    world_name = LaunchConfiguration('world_name')
    lidar_gz_topic = LaunchConfiguration('lidar_gz_topic')
    safety_params = PathJoinSubstitution([
        FindPackageShare('bringup'),
        'config',
        'params.yaml',
    ])

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
    world_name_arg = DeclareLaunchArgument(
        'world_name',
        default_value='villa_world',
        description='Gazebo world name used by spawn/bridge nodes.',
    )
    lidar_gz_topic_arg = DeclareLaunchArgument(
        'lidar_gz_topic',
        default_value=PathJoinSubstitution(['/', robot_id, 'scan']),
        description='Gazebo LaserScan topic to bridge into /<robot_id>/scan.',
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
                'world_name': world_name,
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
                'world_name': world_name,
                'lidar_gz_topic': lidar_gz_topic,
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
                    FindPackageShare('bringup'),
                    'launch',
                    'nav2_robot.launch.py',
                ])
            ),
            launch_arguments={
                'robot_id': robot_id,
                'use_sim_time': use_sim_time,
            }.items(),
        ),
        Node(
            package='coordination',
            executable='cmd_vel_safety_node',
            name=['cmd_vel_safety_', robot_id],
            output='screen',
            parameters=[
                safety_params,
                {'robot_id': robot_id},
                {'use_sim_time': use_sim_time},
            ],
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
        world_name_arg,
        lidar_gz_topic_arg,
        *includes,
    ])
