"""
gazebo_ionic.launch.py
======================
Main entry point for the Fire-Scout Gazebo Ionic simulation.

Usage:
    ros2 launch simulation gazebo_ionic.launch.py
    ros2 launch simulation gazebo_ionic.launch.py headless:=true
    ros2 launch simulation gazebo_ionic.launch.py world:=world_1.sdf

This launch file:
  1. Starts Gazebo Ionic with the chosen world  (gz_world.launch.py)
  2. Spawns robot1 / robot2 / robot3            (spawn_robot.launch.py × 3)
  3. Starts ROS-Gz bridges for each robot       (bridge_robot.launch.py × 3)
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    pkg_sim = get_package_share_directory('simulation')

    # ── Launch arguments ────────────────────────────────────────────────────
    world_arg = DeclareLaunchArgument(
        'world',
        default_value='world_1.sdf',
        description='SDF world file name (must be in simulation/worlds/).',
    )
    headless_arg = DeclareLaunchArgument(
        'headless',
        default_value='false',
        description='Run Gazebo without GUI (server only).',
    )
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulated clock for all nodes.',
    )

    # ── Environment variables ───────────────────────────────────────────────
    ros_share_dir = os.path.dirname(pkg_sim)

    set_gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=f'{pkg_sim}{os.pathsep}{ros_share_dir}',
    )
    set_gz_model_path = SetEnvironmentVariable(
        name='GZ_MODEL_PATH',
        value=f'{os.path.join(pkg_sim, "models")}{os.pathsep}{ros_share_dir}',
    )
    # Avoid FastDDS shared-memory port conflicts in multi-process setup
    set_fastrtps_shm = SetEnvironmentVariable(
        name='FASTDDS_BUILTIN_TRANSPORTS',
        value='UDPv4',
    )

    # ── Sub-launch: world only ──────────────────────────────────────────────
    gz_world = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare('simulation'), 'launch', 'gz_world.launch.py'])
        ),
        launch_arguments={
            'world':    LaunchConfiguration('world'),
            'headless': LaunchConfiguration('headless'),
        }.items(),
    )

    # ── Sub-launch: spawn + bridge for each robot ───────────────────────────
    # Spawn positions match config/robot_spawn_poses.yaml
    robots = [
        {'robot_id': 'robot1', 'spawn_x': '0.0',  'spawn_y': '0.0'},
        {'robot_id': 'robot2', 'spawn_x': '2.0',  'spawn_y': '0.0'},
        {'robot_id': 'robot3', 'spawn_x': '4.0',  'spawn_y': '0.0'},
    ]

    spawn_and_bridge = []
    for r in robots:
        spawn_and_bridge.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [FindPackageShare('simulation'), 'launch', 'spawn_robot.launch.py']
                    )
                ),
                launch_arguments={
                    'robot_id':     r['robot_id'],
                    'spawn_x':      r['spawn_x'],
                    'spawn_y':      r['spawn_y'],
                    'use_sim_time': LaunchConfiguration('use_sim_time'),
                }.items(),
            )
        )
        spawn_and_bridge.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [FindPackageShare('simulation'), 'launch', 'bridge_robot.launch.py']
                    )
                ),
                launch_arguments={
                    'robot_id':     r['robot_id'],
                    'use_sim_time': LaunchConfiguration('use_sim_time'),
                }.items(),
            )
        )

    return LaunchDescription([
        # Arguments
        world_arg,
        headless_arg,
        use_sim_time_arg,
        # Environment
        set_gz_resource_path,
        set_gz_model_path,
        set_fastrtps_shm,
        # World
        gz_world,
        # Robots
        *spawn_and_bridge,
    ])