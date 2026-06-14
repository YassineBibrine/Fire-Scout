from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')

    planners = []
    for robot_id in ('robot1', 'robot2', 'robot3'):
        planners.append(
            Node(
                package='response',
                executable='suppression_planning_node',
                name=f'suppression_planning_node_{robot_id}',
                output='screen',
                parameters=[
                    {'robot_id': robot_id},
                    {'use_sim_time': use_sim_time},
                ],
            )
        )
        planners.append(
            Node(
                package='response',
                executable='rescue_planning_node',
                name=f'rescue_planning_node_{robot_id}',
                output='screen',
                parameters=[
                    {'robot_id': robot_id},
                    {'use_sim_time': use_sim_time},
                ],
            )
        )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true', description='Use simulated clock.'),
        LogInfo(msg=['Global incident fusion contract ready use_sim_time=', use_sim_time]),
        *planners,
    ])
