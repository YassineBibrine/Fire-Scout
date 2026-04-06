from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    robot_id = LaunchConfiguration('robot_id')
    use_sim_time = LaunchConfiguration('use_sim_time')

    slam_status_node = Node(
        package='mapping',
        executable='slam_status_node',
        name='slam_status_node',
        output='screen',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'robot_ids': robot_id},
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument('robot_id', default_value='robot1', description='Robot namespace/id.'),
        DeclareLaunchArgument('use_sim_time', default_value='true', description='Use simulated clock.'),
        slam_status_node,
    ])
