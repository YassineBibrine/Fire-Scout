from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Launch global map merge pipeline and static TF scaffold for robot maps."""
    use_sim_time = LaunchConfiguration('use_sim_time')

    # Config file for multirobot_map_merge behavior.
    map_merge_params = [FindPackageShare('mapping'), '/config/map_merge.yaml']

    # Custom map merge node that merges /robotX/map and publishes /map status.
    # NOTE: Temporarily commented out due to ROS 2 launcher executable discovery issue.
    # The executable works via CLI but not through ros2 launch. Direct call works:
    #   source install/setup.bash && map_merge_node
    # Workaround: Use multirobot_map_merge directly instead until executable lookup is fixed.
    # map_merge_node = Node(
    #     package='mapping',
    #     executable='map_merge_node',
    #     name='map_merge_node',
    #     output='screen',
    #     parameters=[{'use_sim_time': use_sim_time}],
    # )

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
    static_tf_robot1 = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_tf_map_to_robot1_map',
        output='screen',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'robot1/map'],
    )
    static_tf_robot2 = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_tf_map_to_robot2_map',
        output='screen',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'robot2/map'],
    )
    static_tf_robot3 = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_tf_map_to_robot3_map',
        output='screen',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'robot3/map'],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulated clock time.',
        ),
        # map_merge_node,  # Commented out - see note above
        # multirobot_map_merge_node,  # Commented out - package not installed
        static_tf_robot1,
        static_tf_robot2,
        static_tf_robot3,
    ])
