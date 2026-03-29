from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
import os


def generate_launch_description():
    """Launch all Fire-Scout components."""
    
    ld = LaunchDescription()
    
    # TODO: Add your launch nodes and includes here
    # Example:
    # ld.add_action(Node(
    #     package='package_name',
    #     executable='node_name',
    #     name='node_name',
    # ))
    
    return ld
