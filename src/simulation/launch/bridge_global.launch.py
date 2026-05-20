from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    world_name = LaunchConfiguration('world_name')

    world_name_arg = DeclareLaunchArgument(
        'world_name',
        default_value='villa_world',
        description='Gazebo world name used by the clock bridge.',
    )

    def _make_clock_bridge(context, *args, **kwargs):
        world_name_value = world_name.perform(context)
        gz_clock_topic = f"/world/{world_name_value}/clock"
        return [
            Node(
                package='ros_gz_bridge',
                executable='parameter_bridge',
                name='global_clock_bridge',
                output='screen',
                arguments=[
                    f"{gz_clock_topic}@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
                ],
                remappings=[
                    (gz_clock_topic, '/clock'),
                ],
            )
        ]

    return LaunchDescription([
        world_name_arg,
        OpaqueFunction(function=_make_clock_bridge),
    ])
