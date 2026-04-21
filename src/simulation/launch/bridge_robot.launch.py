from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    robot_id = LaunchConfiguration('robot_id')

    robot_id_arg = DeclareLaunchArgument(
        'robot_id',
        default_value='robot1',
        description='Robot namespace/id for ros_gz bridge mapping.',
    )

    info = LogInfo(msg=['Bridge contract active for namespace: ', robot_id])

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='robot_bridge',
        output='screen',
        arguments=[
            ['/model/', robot_id, '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist'],
            ['/model/', robot_id, '/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry'],
            ['/model/', robot_id, '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V'],
        ],
    )

    return LaunchDescription([
        robot_id_arg,
        info,
        bridge,
    ])
