from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    robot_dummy_launch = PathJoinSubstitution([
        FindPackageShare('testing_tools'),
        'launch',
        'robot_dummy_stack.launch.py',
    ])

    robot1_stack = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(robot_dummy_launch),
        launch_arguments={'robot_id': 'robot1', 'use_sim_time': 'true'}.items(),
    )
    robot2_stack = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(robot_dummy_launch),
        launch_arguments={'robot_id': 'robot2', 'use_sim_time': 'true'}.items(),
    )
    robot3_stack = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(robot_dummy_launch),
        launch_arguments={'robot_id': 'robot3', 'use_sim_time': 'true'}.items(),
    )

    dummy_fault_injector = Node(
        package='testing_tools',
        executable='dummy_fault_injector',
        name='dummy_fault_injector',
        output='screen',
        parameters=[{'robot_id': 'robot2', 'use_sim_time': True}],
    )

    dummy_frontier_pub = Node(
        package='testing_tools',
        executable='dummy_frontier_pub',
        name='dummy_frontier_pub',
        output='screen',
        parameters=[{'robot_id': 'robot1', 'use_sim_time': True}],
    )

    namespace_lint_node = Node(
        package='testing_tools',
        executable='namespace_lint_node',
        name='namespace_lint_node',
        output='screen',
    )

    return LaunchDescription([
        robot1_stack,
        robot2_stack,
        robot3_stack,
        dummy_fault_injector,
        dummy_frontier_pub,
        namespace_lint_node,
    ])
