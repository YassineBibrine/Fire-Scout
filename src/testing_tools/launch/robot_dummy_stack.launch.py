from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    robot_id = LaunchConfiguration('robot_id')
    use_sim_time = LaunchConfiguration('use_sim_time')

    robot_id_arg = DeclareLaunchArgument(
        'robot_id',
        default_value='robot1',
        description='Robot namespace/id for dummy publishers.',
    )
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulated clock time.',
    )

    dummy_scan_pub = Node(
        package='testing_tools',
        executable='dummy_scan_pub',
        name='dummy_scan_pub',
        output='screen',
        parameters=[{'robot_id': robot_id, 'use_sim_time': use_sim_time}],
    )

    dummy_odom_pub = Node(
        package='testing_tools',
        executable='dummy_odom_pub',
        name='dummy_odom_pub',
        output='screen',
        parameters=[{'robot_id': robot_id, 'use_sim_time': use_sim_time}],
    )

    dummy_heartbeat_pub = Node(
        package='testing_tools',
        executable='dummy_heartbeat_pub',
        name='dummy_heartbeat_pub',
        output='screen',
        parameters=[{'robot_id': robot_id, 'use_sim_time': use_sim_time}],
    )

    dummy_camera_pub = Node(
        package='testing_tools',
        executable='dummy_camera_pub',
        name='dummy_camera_pub',
        output='screen',
        parameters=[{'robot_id': robot_id, 'use_sim_time': use_sim_time}],
    )
    dummy_esp32_sensor_pub = Node(
        package='testing_tools',
        executable='dummy_esp32_sensor_pub',
        name='dummy_esp32_sensor_pub',
        output='screen',
        parameters=[{'robot_id': robot_id, 'use_sim_time': use_sim_time}],
    )

    return LaunchDescription([
        robot_id_arg,
        use_sim_time_arg,
        dummy_scan_pub,
        dummy_odom_pub,
        dummy_heartbeat_pub,
        dummy_camera_pub,
        dummy_esp32_sensor_pub,
    ])
