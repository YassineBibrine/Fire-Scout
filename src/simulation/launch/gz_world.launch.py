"""
gz_world.launch.py
==================
Launches Gazebo Ionic (gz_sim) with the specified world file.
Can be used standalone or included by gazebo_ionic.launch.py.

Usage:
    ros2 launch simulation gz_world.launch.py
    ros2 launch simulation gz_world.launch.py world:=world_1.sdf headless:=true
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression


def generate_launch_description():

    pkg_sim = get_package_share_directory('simulation')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    # ── Launch arguments ────────────────────────────────────────────────────
    world_arg = DeclareLaunchArgument(
        'world',
        default_value='world_1.sdf',
        description='SDF world filename inside simulation/worlds/.',
    )
    headless_arg = DeclareLaunchArgument(
        'headless',
        default_value='false',
        description='Launch Gazebo server only (no GUI) when true.',
    )

    world_path = os.path.join(pkg_sim, 'worlds', 'world_1.sdf')

    gz_launch_file = os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')

    # ── With GUI ────────────────────────────────────────────────────────────
    gz_sim_gui = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gz_launch_file),
        launch_arguments={
            'gz_args': world_path,
        }.items(),
        condition=UnlessCondition(LaunchConfiguration('headless')),
    )

    # ── Headless (server only) ──────────────────────────────────────────────
    gz_sim_headless = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gz_launch_file),
        launch_arguments={
            'gz_args': ['-s -r ', world_path],
        }.items(),
        condition=IfCondition(LaunchConfiguration('headless')),
    )

    return LaunchDescription([
        world_arg,
        headless_arg,
        gz_sim_gui,
        gz_sim_headless,
    ])