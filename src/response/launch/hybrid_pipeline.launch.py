from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def _truthy(value):
    return str(value).lower() in ('true', '1', 'yes')


def _build_hybrid_nodes(robot_id, use_sim_time, launch_profile, model_path=''):
    pkg_share = get_package_share_directory('response')

    fire_cfg = os.path.join(pkg_share, 'config', 'fire_detection.yaml')
    human_cfg = os.path.join(pkg_share, 'config', 'human_detection.yaml')
    gateway_cfg = os.path.join(pkg_share, 'config', 'sensor_gateway.yaml')
    camera_cfg = os.path.join(pkg_share, 'config', 'camera_inference.yaml')
    fusion_cfg = os.path.join(pkg_share, 'config', 'fusion_decision.yaml')

    profile = str(launch_profile).lower()
    use_mock_camera = profile == 'sim'
    use_real_camera = profile in ('robot', 'debug')

    nodes = [
        Node(
            package='response',
            executable='sensor_gateway_node',
            name=f'sensor_gateway_node_{robot_id}',
            parameters=[
                gateway_cfg,
                {'robot_id': robot_id},
                {'use_sim_time': _truthy(use_sim_time)},
            ],
            output='screen',
        ),
    ]

    if use_mock_camera:
        nodes.append(
            Node(
                package='testing_tools',
                executable='mock_camera_inference_node',
                name=f'mock_camera_inference_node_{robot_id}',
                parameters=[
                    {'robot_id': robot_id},
                    {'use_sim_time': _truthy(use_sim_time)},
                ],
                output='screen',
            )
        )
        nodes.append(
            Node(
                package='testing_tools',
                executable='dummy_esp32_sensor_pub',
                name=f'dummy_esp32_sensor_pub_{robot_id}',
                parameters=[
                    {'robot_id': robot_id},
                    {'use_sim_time': _truthy(use_sim_time)},
                ],
                output='screen',
            )
        )

    if use_real_camera:
        nodes.append(
            Node(
                package='response',
                executable='camera_inference_node',
                name=f'camera_inference_node_{robot_id}',
                parameters=[
                    camera_cfg,
                    {'robot_id': robot_id},
                    {'use_sim_time': _truthy(use_sim_time)},
                    {'model_path': model_path},
                    {'allow_stub_inference': profile == 'debug'},
                ],
                output='screen',
            )
        )

    nodes.extend([
        Node(
            package='response',
            executable='fusion_decision_node',
            name=f'fusion_decision_node_{robot_id}',
            parameters=[
                fusion_cfg,
                {'robot_id': robot_id},
                {'use_sim_time': _truthy(use_sim_time)},
            ],
            output='screen',
        ),
        Node(
            package='response',
            executable='fire_detection_node',
            name=f'fire_detection_node_{robot_id}',
            parameters=[
                fire_cfg,
                {'robot_id': robot_id},
                {'use_sim_time': _truthy(use_sim_time)},
                {'publish_demo_detections': False},
            ],
            output='screen',
        ),
        Node(
            package='response',
            executable='human_detection_node',
            name=f'human_detection_node_{robot_id}',
            parameters=[
                human_cfg,
                {'robot_id': robot_id},
                {'use_sim_time': _truthy(use_sim_time)},
                {'publish_demo_detections': False},
            ],
            output='screen',
        ),
    ])

    return nodes


def _launch_hybrid_nodes(context, *args, **kwargs):
    robot_id = LaunchConfiguration('robot_id').perform(context)
    use_sim_time = LaunchConfiguration('use_sim_time').perform(context)
    launch_profile = LaunchConfiguration('launch_profile').perform(context)
    model_path = LaunchConfiguration('model_path').perform(context)
    return _build_hybrid_nodes(robot_id, use_sim_time, launch_profile, model_path)


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'robot_id',
            default_value='robot1',
            description='Robot namespace.',
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulated clock.',
        ),
        DeclareLaunchArgument(
            'launch_profile',
            default_value='sim',
            description='Hybrid profile: sim uses mock camera inference; robot/debug use real inference.',
        ),
        DeclareLaunchArgument(
            'model_path',
            default_value='',
            description='YOLO model path required by the robot profile.',
        ),
        OpaqueFunction(function=_launch_hybrid_nodes),
    ])
