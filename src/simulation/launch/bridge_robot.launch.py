from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """
    Launch the ROS ↔ Gazebo Ionic bridge for a single robot namespace.

    Topics bridged per robot:
      cmd_vel   : ROS → Gz  (geometry_msgs/Twist)
      odom      : Gz  → ROS (nav_msgs/Odometry)
      tf        : Gz  → ROS (tf2_msgs/TFMessage)
      scan      : Gz  → ROS (sensor_msgs/LaserScan)
      imu       : Gz  → ROS (sensor_msgs/Imu)
      camera    : Gz  → ROS (sensor_msgs/Image)
    """
    robot_id = LaunchConfiguration('robot_id')
    use_sim_time = LaunchConfiguration('use_sim_time')

    robot_id_arg = DeclareLaunchArgument(
        'robot_id',
        default_value='robot1',
        description='Robot namespace/id for ros_gz bridge mapping.',
    )
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulated clock.',
    )

    info = LogInfo(msg=['[bridge_robot] Bridging Gazebo ↔ ROS topics for namespace: ', robot_id])

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name=['robot_bridge_', robot_id],
        namespace=robot_id,
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
        arguments=[
            # ── cmd_vel : ROS → Gazebo ──────────────────────────────────────
            ['/model/', robot_id, '/cmd_vel'
             '@geometry_msgs/msg/Twist'
             ']gz.msgs.Twist'],

            # ── odometry : Gazebo → ROS ─────────────────────────────────────
            ['/model/', robot_id, '/odometry'
             '@nav_msgs/msg/Odometry'
             '[gz.msgs.Odometry'],

            # ── TF : Gazebo → ROS ───────────────────────────────────────────
            ['/model/', robot_id, '/tf'
             '@tf2_msgs/msg/TFMessage'
             '[gz.msgs.Pose_V'],

            # ── LiDAR scan : Gazebo → ROS ───────────────────────────────────
            ['/model/', robot_id, '/scan'
             '@sensor_msgs/msg/LaserScan'
             '[gz.msgs.LaserScan'],

            # ── IMU : Gazebo → ROS ──────────────────────────────────────────
            ['/model/', robot_id, '/imu'
             '@sensor_msgs/msg/Imu'
             '[gz.msgs.IMU'],

            # ── Camera image : Gazebo → ROS ─────────────────────────────────
            ['/model/', robot_id, '/camera'
             '@sensor_msgs/msg/Image'
             '[gz.msgs.Image'],
        ],
        remappings=[
            # Remap from Gazebo model paths to clean robot namespace topics
            (['/model/', robot_id, '/cmd_vel'],    ['/', robot_id, '/cmd_vel']),
            (['/model/', robot_id, '/odometry'],   ['/', robot_id, '/odom']),
            (['/model/', robot_id, '/tf'],         ['/', robot_id, '/tf']),
            (['/model/', robot_id, '/scan'],       ['/', robot_id, '/scan']),
            (['/model/', robot_id, '/imu'],        ['/', robot_id, '/imu']),
            (['/model/', robot_id, '/camera'],     ['/', robot_id, '/camera']),
        ],
    )

    return LaunchDescription([
        robot_id_arg,
        use_sim_time_arg,
        info,
        bridge,
    ])