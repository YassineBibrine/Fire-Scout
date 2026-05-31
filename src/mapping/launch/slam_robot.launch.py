from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Launch per-robot SLAM stack (slam_toolbox + wrapper relay node)."""
    # robot_id is required by policy and intentionally has no default.
    robot_id = LaunchConfiguration('robot_id')
    use_sim_time = LaunchConfiguration('use_sim_time')

    # Centralized slam_toolbox YAML shared by all robots.
    slam_params = PathJoinSubstitution([
        FindPackageShare('mapping'),
        'config',
        'slam_toolbox_robot.yaml',
    ])

    # Launch slam_toolbox in online async mode and remap canonical topics to
    # this specific robot namespace.
    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name=['slam_toolbox_', robot_id],
        output='screen',
        parameters=[
            slam_params,
            {'use_sim_time': use_sim_time},
            {'odom_frame': PathJoinSubstitution([robot_id, 'odom'])},
            {'map_frame': PathJoinSubstitution([robot_id, 'map'])},
            {'base_frame': PathJoinSubstitution([robot_id, 'base_link'])},
            {'transform_publish_period': 0.02},
            {'transform_timeout': 0.2},
            {'tf_buffer_duration': 30.0},
            # Override the YAML's broken placeholder /robotX/scan with the
            # real relay topic produced by slam_wrapper_node. This must come
            # after slam_params so it wins the last-write-wins parameter merge.
            {'scan_topic': PathJoinSubstitution(['/', robot_id, 'slam', 'scan'])},
        ],
        remappings=[
            ('/scan', PathJoinSubstitution(['/', robot_id, 'slam', 'scan'])),
            ('/odom', PathJoinSubstitution(['/', robot_id, 'slam', 'odom'])),
            ('/map', PathJoinSubstitution(['/', robot_id, 'map'])),
        ],
    )



    # Launch the wrapper node that relays topics and publishes health status.
    slam_wrapper_node = Node(
        package='mapping',
        executable='slam_wrapper_node',
        name=['slam_wrapper_', robot_id],
        output='screen',
        parameters=[
            {'robot_id': robot_id, 'use_sim_time': use_sim_time},
            {'use_global_lidar': False},
        ],
    )

    lidar_static_tf_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name=['static_tf_', robot_id, '_base_link_to_lidar'],
        output='screen',
        arguments=[
            '0',
            '0',
            '0.2',
            '0',
            '0',
            '0',
            PathJoinSubstitution([robot_id, 'base_link']),
            PathJoinSubstitution([robot_id, 'lidar']),
        ],
        parameters=[{'use_sim_time': use_sim_time}],
    )

    camera_static_tf_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name=['static_tf_', robot_id, '_base_link_to_camera'],
        output='screen',
        arguments=[
            '0.10',
            '0',
            '0.15',
            '0',
            '0',
            '0',
            PathJoinSubstitution([robot_id, 'base_link']),
            PathJoinSubstitution([robot_id, 'camera']),
        ],
        parameters=[{'use_sim_time': use_sim_time}],
    )

    def _launch_lifecycle_manager(context, *args, **kwargs):
        robot_id_value = robot_id.perform(context)
        return [
            Node(
                package='nav2_lifecycle_manager',
                executable='lifecycle_manager',
                name=f'slam_toolbox_manager_{robot_id_value}',
                output='screen',
                parameters=[
                    {'use_sim_time': use_sim_time},
                    {'autostart': True},
                    {'node_names': [f'slam_toolbox_{robot_id_value}']},
                ],
            )
        ]

    return LaunchDescription([
        DeclareLaunchArgument(
            'robot_id',
            description='Required robot namespace/id (example: robot1, robot2, robot3).',
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulated clock time.',
        ),
        slam_toolbox_node,
        slam_wrapper_node,
        lidar_static_tf_node,
        camera_static_tf_node,
        OpaqueFunction(function=_launch_lifecycle_manager),
    ])
