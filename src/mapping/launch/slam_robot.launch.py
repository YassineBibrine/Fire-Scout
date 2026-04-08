from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Launch per-robot SLAM stack (slam_toolbox + wrapper relay node)."""
    # robot_id is required by policy and intentionally has no default.
    robot_id = LaunchConfiguration('robot_id')
    use_sim_time = LaunchConfiguration('use_sim_time')

    # Centralized slam_toolbox YAML shared by all robots.
    slam_params = [FindPackageShare('mapping'), '/config/slam_toolbox_robot.yaml']

    # Launch slam_toolbox in online async mode and remap canonical topics to
    # this specific robot namespace.
    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[slam_params, {'use_sim_time': use_sim_time}],
        remappings=[
            ('/scan', ['/', robot_id, '/scan']),
            ('/odom', ['/', robot_id, '/odom']),
            ('/map', ['/', robot_id, '/map']),
        ],
    )

    # Launch the wrapper node that relays topics and publishes health status.
    slam_wrapper_node = Node(
        package='mapping',
        executable='slam_wrapper_node',
        name='slam_wrapper_node',
        output='screen',
        parameters=[{'robot_id': robot_id, 'use_sim_time': use_sim_time}],
    )

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
    ])
