from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    pkg_share = get_package_share_directory('response')

    # ----------------------------------------------------------------
    # Config paths
    # ----------------------------------------------------------------
    fire_cfg = os.path.join(pkg_share, 'config', 'fire_detection.yaml')
    human_cfg = os.path.join(pkg_share, 'config', 'human_detection.yaml')
    gateway_cfg = os.path.join(pkg_share, 'config', 'sensor_gateway.yaml')
    camera_cfg = os.path.join(pkg_share, 'config', 'camera_inference.yaml')
    fusion_cfg = os.path.join(pkg_share, 'config', 'fusion_decision.yaml')

    # ----------------------------------------------------------------
    # Arguments
    # ----------------------------------------------------------------
    robot_id = LaunchConfiguration('robot_id')
    use_sim_time = LaunchConfiguration('use_sim_time')

    # ----------------------------------------------------------------
    # Phase 2 hybrid pipeline nodes (per robot)
    # ----------------------------------------------------------------

    sensor_gateway = Node(
        package='response',
        executable='sensor_gateway_node',
        name='sensor_gateway_node',
        parameters=[
            gateway_cfg,
            {'robot_id': robot_id},
            {'use_sim_time': use_sim_time},
        ],
        output='screen',
    )

    camera_inference = Node(
        package='response',
        executable='camera_inference_node',
        name='camera_inference_node',
        parameters=[
            camera_cfg,
            {'robot_id': robot_id},
            {'use_sim_time': use_sim_time},
        ],
        output='screen',
    )

    fusion_decision = Node(
        package='response',
        executable='fusion_decision_node',
        name='fusion_decision_node',
        parameters=[
            fusion_cfg,
            {'robot_id': robot_id},
            {'use_sim_time': use_sim_time},
        ],
        output='screen',
    )

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
        # Sensor layer
        sensor_gateway,
        camera_inference,
        # Fusion layer
        fusion_decision,
        # Detection layer (downstream of fusion)
        fire_detection,
        human_detection,
    ])

