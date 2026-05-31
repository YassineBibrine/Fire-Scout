import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('response')

    # ----------------------------------------------------------------
    # Config paths
    # ----------------------------------------------------------------
    fire_cfg = os.path.join(pkg_share, 'config', 'fire_detection.yaml')
    human_cfg = os.path.join(pkg_share, 'config', 'human_detection.yaml')

    # ----------------------------------------------------------------
    # Arguments
    # ----------------------------------------------------------------
    robot_id = LaunchConfiguration('robot_id')
    use_sim_time = LaunchConfiguration('use_sim_time')

    # ----------------------------------------------------------------
    # Detection nodes (consume FusionDecision; demo mode kept for CI)
    # ----------------------------------------------------------------

    fire_detection = Node(
        package='response',
        executable='fire_detection_node',
        name='fire_detection_node',
        parameters=[
            fire_cfg,
            {'robot_id': robot_id},
            {'use_sim_time': use_sim_time},
            {'publish_demo_detections': False},
        ],
        output='screen',
    )

    human_detection = Node(
        package='response',
        executable='human_detection_node',
        name='human_detection_node',
        parameters=[
            human_cfg,
            {'robot_id': robot_id},
            {'use_sim_time': use_sim_time},
            {'publish_demo_detections': False},
        ],
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'robot_id',
            default_value='robot1',
            description='Robot namespace',
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulated clock.',
        ),
        # Detection layer (downstream of fusion)
        fire_detection,
        human_detection,
    ])

