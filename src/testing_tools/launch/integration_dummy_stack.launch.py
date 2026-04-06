from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    stacks = []
    for robot_id in ('robot1', 'robot2', 'robot3'):
        stacks.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution([
                        FindPackageShare('testing_tools'),
                        'launch',
                        'robot_dummy_stack.launch.py',
                    ])
                ),
                launch_arguments={'robot_id': robot_id}.items(),
            )
        )

    return LaunchDescription([
        *stacks,
    ])
