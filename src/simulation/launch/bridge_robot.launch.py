from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo, OpaqueFunction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    robot_id = LaunchConfiguration('robot_id')
    world_name = LaunchConfiguration('world_name')
    lidar_gz_topic = LaunchConfiguration('lidar_gz_topic')

    robot_id_arg = DeclareLaunchArgument(
        'robot_id',
        default_value='robot1',
        description='Robot namespace/id for ros_gz bridge mapping.',
    )
    world_name_arg = DeclareLaunchArgument(
        'world_name',
        default_value='villa_world',
        description='Gazebo world name hosting the robot models.',
    )
    lidar_gz_topic_arg = DeclareLaunchArgument(
        'lidar_gz_topic',
        default_value=PathJoinSubstitution(['/', robot_id, 'scan']),
        description='Gazebo LaserScan topic to bridge into /<robot_id>/scan.',
    )
    info = LogInfo(msg=['Bridge contract active for namespace: ', robot_id])

    def _make_robot_bridge(context, *args, **kwargs):
        robot_id_value = robot_id.perform(context)
        lidar_gz_value = lidar_gz_topic.perform(context)
        gz_cmd_vel_topic = f"/model/{robot_id_value}/cmd_vel"
        gz_odom_topic = f"/model/{robot_id_value}/odometry"

        return [
            Node(
                package='ros_gz_bridge',
                executable='parameter_bridge',
                name=f"robot_bridge_{robot_id_value}",
                output='screen',
                arguments=[
                    f"{gz_cmd_vel_topic}@geometry_msgs/msg/Twist]gz.msgs.Twist",
                    f"{gz_odom_topic}@nav_msgs/msg/Odometry[gz.msgs.Odometry",
                    f"{lidar_gz_value}@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
                ],
                remappings=[
                    (gz_cmd_vel_topic, f"/{robot_id_value}/cmd_vel_safe"),
                    (gz_odom_topic, f"/{robot_id_value}/odom"),
                    (lidar_gz_value, f"/{robot_id_value}/scan"),
                ],
            )
        ]

    return LaunchDescription([
        robot_id_arg,
        world_name_arg,
        lidar_gz_topic_arg,
        info,
        OpaqueFunction(function=_make_robot_bridge),
    ])
