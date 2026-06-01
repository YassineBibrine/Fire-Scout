from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Launch global map merge pipeline and static TF scaffold for robot maps."""
    use_sim_time = LaunchConfiguration('use_sim_time')
    robot_ids = ('robot1', 'robot2', 'robot3')

    # Config file for multirobot_map_merge behavior.
    map_merge_params = PathJoinSubstitution([
        FindPackageShare('mapping'), 'config', 'map_merge.yaml'
    ])

    # Custom map merge node that merges /robotX/map and publishes /map status.
    map_merge_node = Node(
        package='mapping',
        executable='map_merge_node',
        name='map_merge_node',
        output='screen',
        parameters=[map_merge_params, {'use_sim_time': use_sim_time}, {'robot_ids': list(robot_ids)}],
    )


    # multirobot_map_merge backend configured from YAML.
    # NOTE: multirobot_map_merge package not installed in system, commenting out for now.
    # To enable, install: sudo apt install ros-kilted-multirobot-map-merge
    # multirobot_map_merge_node = Node(
    #     package='multirobot_map_merge',
    #     executable='map_merge',
    #     name='multirobot_map_merge',
    #     output='screen',
    #     parameters=[map_merge_params, {'use_sim_time': use_sim_time}],
    # )

    # Identity static TF placeholders map -> robotX/map as initial alignment.
    static_tfs = [
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name=f'static_tf_map_to_{robot_id}_map',
            output='screen',
            arguments=['0', '0', '0', '0', '0', '0', 'map', f'{robot_id}/map'],
            parameters=[{'use_sim_time': use_sim_time}],
        )
        for robot_id in robot_ids
    ]

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulated clock time.',
        ),
        map_merge_node,
        # multirobot_map_merge_node,  # Commented out - package not installed
        *static_tfs,
    ])
