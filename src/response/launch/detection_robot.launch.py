from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    robot_id = LaunchConfiguration('robot_id')

    # Get config file path correctly
    pkg_share = get_package_share_directory('response')

    config_file = os.path.join(
        pkg_share,
        'config',
        'fire_detection.yaml'
    )

    return LaunchDescription([

        DeclareLaunchArgument(
            'robot_id',
            default_value='robot1',
            description='Robot namespace'
        ),

        Node(
            package='response',
            executable='fire_detection_node',
            name='fire_detection_node',

            namespace=robot_id,

            parameters=[
                config_file,
                {'robot_id': robot_id}
            ],

            output='screen'
        )

    ])
