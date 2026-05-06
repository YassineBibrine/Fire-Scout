from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    world_name = LaunchConfiguration('world_name')

    world_name_arg = DeclareLaunchArgument(
        'world_name',
        default_value='villa_world',
        description='Gazebo world name used by the clock bridge.',
    )

    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='global_clock_bridge',
        output='screen',
        parameters=[
            {'bridge_names': ['clock']},
            {
                'bridges.clock.ros_topic_name': '/clock',
                'bridges.clock.gz_topic_name': PathJoinSubstitution(['/world', world_name, 'clock']),
                'bridges.clock.ros_type_name': 'rosgraph_msgs/msg/Clock',
                'bridges.clock.gz_type_name': 'gz.msgs.Clock',
                'bridges.clock.direction': 'GZ_TO_ROS',
            },
        ],
    )

    return LaunchDescription([
        world_name_arg,
        clock_bridge,
    ])
