from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    robot_id = LaunchConfiguration('robot_id')
    use_sim_time = LaunchConfiguration('use_sim_time')

    nav2_params = PathJoinSubstitution([
        FindPackageShare('bringup'),
        'config',
        'nav2_params.yaml',
    ])

    bt_nav_to_pose = PathJoinSubstitution([
        FindPackageShare('nav2_bt_navigator'),
        'behavior_trees',
        'navigate_w_replanning_and_recovery.xml',
    ])
    bt_nav_through_poses = PathJoinSubstitution([
        FindPackageShare('nav2_bt_navigator'),
        'behavior_trees',
        'navigate_through_poses_w_replanning_and_recovery.xml',
    ])

    controller_server = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        namespace=robot_id,
        output='screen',
        parameters=[nav2_params, {'use_sim_time': use_sim_time}],
    )

    planner_server = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        namespace=robot_id,
        output='screen',
        parameters=[nav2_params, {'use_sim_time': use_sim_time}],
    )

    bt_navigator = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        namespace=robot_id,
        output='screen',
        parameters=[
            nav2_params,
            {'use_sim_time': use_sim_time},
            {
                'default_nav_to_pose_bt_xml': bt_nav_to_pose,
                'default_nav_through_poses_bt_xml': bt_nav_through_poses,
            },
        ],
    )

    behavior_server = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        name='behavior_server',
        namespace=robot_id,
        output='screen',
        parameters=[nav2_params, {'use_sim_time': use_sim_time}],
    )

    waypoint_follower = Node(
        package='nav2_waypoint_follower',
        executable='waypoint_follower',
        name='waypoint_follower',
        namespace=robot_id,
        output='screen',
        parameters=[nav2_params, {'use_sim_time': use_sim_time}],
    )

    velocity_smoother = Node(
        package='nav2_velocity_smoother',
        executable='velocity_smoother',
        name='velocity_smoother',
        namespace=robot_id,
        output='screen',
        parameters=[nav2_params, {'use_sim_time': use_sim_time}],
    )

    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='nav2_lifecycle_manager',
        namespace=robot_id,
        output='screen',
        parameters=[
            {'use_sim_time': use_sim_time},
            {
                'autostart': True,
                'node_names': [
                    'controller_server',
                    'planner_server',
                    'bt_navigator',
                    'behavior_server',
                    'waypoint_follower',
                    'velocity_smoother',
                ],
            },
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'robot_id',
            default_value='robot1',
            description='Robot namespace/id.',
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulated clock time.',
        ),
        controller_server,
        planner_server,
        bt_navigator,
        behavior_server,
        waypoint_follower,
        velocity_smoother,
        lifecycle_manager,
    ])
