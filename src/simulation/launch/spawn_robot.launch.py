from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    robot_id = LaunchConfiguration('robot_id')
    spawn_x = LaunchConfiguration('spawn_x')
    spawn_y = LaunchConfiguration('spawn_y')
    use_sim_time = LaunchConfiguration('use_sim_time')

    robot_id_arg = DeclareLaunchArgument(
        'robot_id',
        default_value='robot1',
        description='Robot namespace/id.',
    )
    spawn_x_arg = DeclareLaunchArgument(
        'spawn_x',
        default_value='0.0',
        description='Robot spawn X coordinate in Gazebo.',
    )
    spawn_y_arg = DeclareLaunchArgument(
        'spawn_y',
        default_value='0.0',
        description='Robot spawn Y coordinate in Gazebo.',
    )
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulated clock.',
    )

    # Use local Fire-Scout diff-drive model with moderate size for this world.
    pkg_sim = get_package_share_directory('simulation')
    model_file = os.path.join(
        pkg_sim,
        'models',
        'model.sdf',
    )

    spawn = Node(
        package='ros_gz_sim',
        executable='create',
        name='spawn_entity',
        output='screen',
        arguments=[
            '-name', robot_id,
            '-file', model_file,
            '-x', spawn_x,
            '-y', spawn_y,
            '-z', '0.1',
        ],
        parameters=[{'use_sim_time': use_sim_time}],
    )

    return LaunchDescription([
        robot_id_arg,
        spawn_x_arg,
        spawn_y_arg,
        use_sim_time_arg,
        spawn,
    ])
