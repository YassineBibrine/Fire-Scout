from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.actions import TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    robot_id = LaunchConfiguration('robot_id')
    use_sim_time = LaunchConfiguration('use_sim_time')
    spawn_robot = LaunchConfiguration('spawn_robot')

    world_arg = DeclareLaunchArgument(
        'world',
        default_value=PathJoinSubstitution([
            FindPackageShare('simulation'),
            'worlds',
            'firescout_env.world',
        ]),
        description='Path to the Gazebo world file',
    )

    robot_id_arg = DeclareLaunchArgument(
        'robot_id',
        default_value='robot1',
        description='Robot namespace/id to spawn.',
    )

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulated clock.',
    )

    spawn_robot_arg = DeclareLaunchArgument(
        'spawn_robot',
        default_value='true',
        description='Spawn a default TurtleBot in Gazebo.',
    )

    gz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py',
            ])
        ),
        launch_arguments={
            'gz_args': ['-r ', LaunchConfiguration('world')],
        }.items(),
    )

    spawn_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('simulation'),
                'launch',
                'spawn_robot.launch.py',
            ])
        ),
        condition=IfCondition(spawn_robot),
        launch_arguments={
            'robot_id': robot_id,
            'use_sim_time': use_sim_time,
        }.items(),
    )

    delayed_spawn = TimerAction(period=3.0, actions=[spawn_launch])

    return LaunchDescription([
        world_arg,
        robot_id_arg,
        use_sim_time_arg,
        spawn_robot_arg,
        gz_launch,
        delayed_spawn,
    ])
