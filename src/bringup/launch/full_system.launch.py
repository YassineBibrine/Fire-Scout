from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import TimerAction
from launch.actions import GroupAction
from launch.actions import IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    simulation = LaunchConfiguration('simulation')
    use_sim_time = LaunchConfiguration('use_sim_time')
    world_name = LaunchConfiguration('world_name')

    simulation_arg = DeclareLaunchArgument(
        'simulation',
        default_value='true',
        description='Run simulation stack when true.',
    )
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulated clock.',
    )
    world_name_arg = DeclareLaunchArgument(
        'world_name',
        default_value='villa_world',
        description='Gazebo world name used by spawn/bridge nodes.',
    )
    global_stack = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('bringup'),
                'launch',
                'global_stack.launch.py',
            ])
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'simulation': simulation,
        }.items(),
    )

    simulation_world = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('simulation'),
                'launch',
                'sim.launch.py',
            ])
        ),
        condition=IfCondition(simulation),
    )

    robot_groups = []
    robot_specs = (
        ('robot1', '-2.0', '-2.0'),
        ('robot2', '0.0', '-2.0'),
        ('robot3', '2.0', '-2.0'),
    )
    for index, (robot_id, spawn_x, spawn_y) in enumerate(robot_specs):
        robot_stack = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('bringup'),
                    'launch',
                    'robot_stack.launch.py',
                ])
            ),
            launch_arguments={
                'simulation': simulation,
                'robot_id': robot_id,
                'spawn_x': spawn_x,
                'spawn_y': spawn_y,
                'use_sim_time': use_sim_time,
                'world_name': world_name,
            }.items(),
        )
        robot_group = GroupAction([
            PushRosNamespace(robot_id),
            robot_stack,
        ])

        robot_groups.append(
            TimerAction(
                period=8.0 + 4.0 * index,
                actions=[robot_group],
            )
        )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
        arguments=['-d', PathJoinSubstitution([
            FindPackageShare('bringup'), 'config', 'firescout_viz.rviz'
        ])],
    )

    return LaunchDescription([
        simulation_arg,
        use_sim_time_arg,
        world_name_arg,
        simulation_world,
        global_stack,
        *robot_groups,
        rviz_node,
    ])
