from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    robot_id = LaunchConfiguration('robot_id')

    robot_id_arg = DeclareLaunchArgument(
        'robot_id',
        default_value='robot1',
        description='Robot namespace/id for ros_gz bridge mapping.',
    )

    # This launch file intentionally logs the contract endpoint.
    # Each team should add ros_gz_bridge parameter_bridge instances here.
    info = LogInfo(msg=['Bridge contract active for namespace: ', robot_id])

    return LaunchDescription([
        robot_id_arg,
        info,
    ])
