from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='global_clock_bridge',
        output='screen',
        parameters=[
            {'bridge_names': ['clock']},
            {
                'bridges.clock.ros_topic_name': '/clock',
                'bridges.clock.gz_topic_name': '/world/villa_world/clock',
                'bridges.clock.ros_type_name': 'rosgraph_msgs/msg/Clock',
                'bridges.clock.gz_type_name': 'gz.msgs.Clock',
                'bridges.clock.direction': 'GZ_TO_ROS',
            },
        ],
    )

    return LaunchDescription([
        clock_bridge,
    ])
