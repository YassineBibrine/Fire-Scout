from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    robot_id = LaunchConfiguration('robot_id')

    return LaunchDescription([
        DeclareLaunchArgument('robot_id', default_value='robot1', description='Robot namespace/id.'),
        Node(package='testing_tools', executable='dummy_scan_pub', name='dummy_scan_pub', namespace=robot_id),
        Node(package='testing_tools', executable='dummy_odom_pub', name='dummy_odom_pub', namespace=robot_id),
        Node(package='testing_tools', executable='dummy_camera_pub', name='dummy_camera_pub', namespace=robot_id),
        Node(
            package='testing_tools',
            executable='dummy_heartbeat_pub',
            name='dummy_heartbeat_pub',
            namespace=robot_id,
            parameters=[{'robot_id': robot_id}],
        ),
    ])
