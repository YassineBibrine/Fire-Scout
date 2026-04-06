from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    robot_id = LaunchConfiguration('robot_id')

    robot_id_arg = DeclareLaunchArgument(
        'robot_id',
        default_value='robot1',
        description='Robot namespace/id for ros_gz bridge mapping.',
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='bridge_topics',
        output='screen',
        arguments=[
            [robot_id, '/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan'],
            [robot_id, '/odom@nav_msgs/msg/Odometry@gz.msgs.Odometry'],
            [robot_id, '/camera/image_raw@sensor_msgs/msg/Image@gz.msgs.Image'],
            '/clock@rosgraph_msgs/msg/Clock@gz.msgs.Clock',
        ],
    )

    return LaunchDescription([
        robot_id_arg,
        bridge,
    ])
