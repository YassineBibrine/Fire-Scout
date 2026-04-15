from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    return LaunchDescription([

        Node(
            package='ros_gz_sim',
            executable='create',
            arguments=[
                '-name', 'turtlebot3',
                '-topic', 'robot_description',
                '-x', '0',
                '-y', '0',
                '-z', '0.2'
            ],
            output='screen'
        )
    ])