from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, TextSubstitution
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

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name=[TextSubstitution(text='robot_bridge_'), robot_id],
        output='screen',
        parameters=[
            {'bridge_names': ['cmd_vel', 'odometry', 'lidar']},
            {
                'bridges.cmd_vel.ros_topic_name': PathJoinSubstitution(['/', robot_id, 'cmd_vel_safe']),
                'bridges.cmd_vel.gz_topic_name': PathJoinSubstitution(['/model', robot_id, 'cmd_vel']),
                'bridges.cmd_vel.ros_type_name': 'geometry_msgs/msg/Twist',
                'bridges.cmd_vel.gz_type_name': 'gz.msgs.Twist',
                'bridges.cmd_vel.direction': 'ROS_TO_GZ',
            },
            {
                'bridges.odometry.ros_topic_name': PathJoinSubstitution(['/', robot_id, 'odom']),
                'bridges.odometry.gz_topic_name': PathJoinSubstitution(['/model', robot_id, 'odometry']),
                'bridges.odometry.ros_type_name': 'nav_msgs/msg/Odometry',
                'bridges.odometry.gz_type_name': 'gz.msgs.Odometry',
                'bridges.odometry.direction': 'GZ_TO_ROS',
            },
            {
                'bridges.lidar.ros_topic_name': PathJoinSubstitution(['/', robot_id, 'scan']),
                'bridges.lidar.gz_topic_name': lidar_gz_topic,
                'bridges.lidar.ros_type_name': 'sensor_msgs/msg/LaserScan',
                'bridges.lidar.gz_type_name': 'gz.msgs.LaserScan',
                'bridges.lidar.direction': 'GZ_TO_ROS',
            },
        ],
    )

    return LaunchDescription([
        robot_id_arg,
        world_name_arg,
        lidar_gz_topic_arg,
        info,
        bridge,
    ])
