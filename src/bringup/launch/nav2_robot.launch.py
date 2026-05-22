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

    # NOTE: We intentionally do NOT chain controller_server -> velocity_smoother.
    # The MPPI controller already enforces velocity/acceleration limits and
    # cmd_vel_safety_node performs the final safety filtering on /<robot>/cmd_vel
    # before the Gazebo bridge consumes /<robot>/cmd_vel_safe. Adding the
    # nav2_velocity_smoother lifecycle node was making robotN.nav2_lifecycle_manager
    # block indefinitely on velocity_smoother/get_state under heavy startup load.
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
                'service_timeout': 30.0,
                'bond_timeout': 10.0,
                'node_names': [
                    'controller_server',
                    'planner_server',
                    'bt_navigator',
                    'behavior_server',
                    'waypoint_follower',
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
        lifecycle_manager,
    ])
