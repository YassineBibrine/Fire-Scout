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

    human_config_file = os.path.join(
        pkg_share,
        'config',
        'human_detection.yaml'
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
            parameters=[
                config_file,
                {'robot_id': robot_id},
                {'publish_demo_detections': False}
            ],

            output='screen'
        ),

        Node(
            package='response',
            executable='human_detection_node',
            name='human_detection_node',
            parameters=[
                human_config_file,
                {'robot_id': robot_id},
                {'publish_demo_detections': False}
            ],

            output='screen'
        ),

        Node(
            package='response',
            executable='suppression_planning_node',
            name='suppression_planning_node',
            parameters=[
                {'robot_id': robot_id}
            ],

            output='screen'
        ),

        Node(
            package='response',
            executable='rescue_planning_node',
            name='rescue_planning_node',
            parameters=[
                {'robot_id': robot_id}
            ],

            output='screen'
        )

    ])
