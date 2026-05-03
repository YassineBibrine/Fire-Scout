"""
spawn_robot.launch.py  (FIXED)
==============================
Fix applied:
  - Spawn node name is now unique per robot: 'spawn_entity_<robot_id>'
    instead of the hardcoded 'spawn_entity' shared by all 3 robots.
  - Added -z 0.1 (already present) and kept all existing args.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    robot_id     = LaunchConfiguration('robot_id')
    spawn_x      = LaunchConfiguration('spawn_x')
    spawn_y      = LaunchConfiguration('spawn_y')
    use_sim_time = LaunchConfiguration('use_sim_time')

    robot_id_arg = DeclareLaunchArgument(
        'robot_id',
        default_value='robot1',
        description='Robot namespace / Gazebo model name.',
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

    pkg_sim    = get_package_share_directory('simulation')
    model_file = os.path.join(pkg_sim, 'models', 'model.sdf')

    spawn = Node(
        package='ros_gz_sim',
        executable='create',
        # FIX: unique name per robot → avoids ROS node-name collision
        name=['spawn_entity_', robot_id],
        output='screen',
        arguments=[
            '-name',  robot_id,
            '-file',  model_file,
            '-x',     spawn_x,
            '-y',     spawn_y,
            '-z',     '0.1',
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