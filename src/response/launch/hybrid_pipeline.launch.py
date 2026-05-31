from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    pkg_share = get_package_share_directory('response')

    gateway_cfg = os.path.join(pkg_share, 'config', 'sensor_gateway.yaml')
    camera_cfg = os.path.join(pkg_share, 'config', 'camera_inference.yaml')
    fusion_cfg = os.path.join(pkg_share, 'config', 'fusion_decision.yaml')

    robot_id = LaunchConfiguration('robot_id')
    use_sim_time = LaunchConfiguration('use_sim_time')
    launch_profile = LaunchConfiguration('launch_profile')

    use_mock_camera = PythonExpression(["'", launch_profile, "' == 'sim'"])

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

    mock_camera_inference = Node(
        package='testing_tools',
        executable='mock_camera_inference_node',
        name='mock_camera_inference_node',
        parameters=[
            {'robot_ids': [robot_id]},
            {'use_sim_time': use_sim_time},
        ],
        output='screen',
        condition=IfCondition(use_mock_camera),
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
        condition=UnlessCondition(use_mock_camera),
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
        DeclareLaunchArgument(
            'launch_profile',
            default_value='sim',
            description='Launch profile: sim, robot, or debug.',
        ),
        sensor_gateway,
        mock_camera_inference,
        camera_inference,
        fusion_decision,
    ])
