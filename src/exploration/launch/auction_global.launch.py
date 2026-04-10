from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    auction_config = PathJoinSubstitution([FindPackageShare('exploration'), 'config', 'auction.yaml'])

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true', description='Use simulated clock.'),
        Node(
            package='exploration',
            executable='auctioneer_node',
            name='auctioneer',
            namespace='coordination',
            parameters=[auction_config, {'use_sim_time': use_sim_time}],
            output='screen',
        ),
    ])
