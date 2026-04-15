from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    robot_id = LaunchConfiguration('robot_id')
    use_sim_time = LaunchConfiguration('use_sim_time')
    frontier_config = PathJoinSubstitution([FindPackageShare('exploration'), 'config', 'frontier.yaml'])

    return LaunchDescription([
        DeclareLaunchArgument('robot_id', default_value='robot1', description='Robot namespace/id.'),
        DeclareLaunchArgument('use_sim_time', default_value='true', description='Use simulated clock.'),
        Node(
            package='exploration',
            executable='frontier_detector_node',
            name='frontier_detector',
            namespace=robot_id,
            parameters=[frontier_config, {'use_sim_time': use_sim_time, 'robot_id': robot_id}],
            output='screen',
        ),
        Node(
            package='exploration',
            executable='bidder_node',
            name='bidder',
            namespace=robot_id,
            parameters=[frontier_config, {'use_sim_time': use_sim_time, 'robot_id': robot_id}],
            output='screen',
        ),
    ])
