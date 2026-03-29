from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    robot_id = LaunchConfiguration('robot_id')
    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        DeclareLaunchArgument('robot_id', default_value='robot1', description='Robot namespace/id.'),
        DeclareLaunchArgument('use_sim_time', default_value='true', description='Use simulated clock.'),
        LogInfo(msg=['Mapping contract ready for ', robot_id, ' use_sim_time=', use_sim_time]),
    ])
