from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulated clock time.'
    )

    mission_policy_yaml = [FindPackageShare('coordination'), '/config/mission_policy.yaml']
    fault_policy_yaml = [FindPackageShare('coordination'), '/config/fault_policy.yaml']
    allocator_yaml = [FindPackageShare('coordination'), '/config/allocator.yaml']

    mission_manager = Node(
        package='coordination',
        executable='mission_manager_node',
        name='mission_manager',
        namespace='coordination',
        output='screen',
        parameters=[mission_policy_yaml, {'use_sim_time': use_sim_time}],
    )

    health_monitor = Node(
        package='coordination',
        executable='health_monitor_node',
        name='health_monitor',
        namespace='coordination',
        output='screen',
        parameters=[fault_policy_yaml, {'use_sim_time': use_sim_time}],
    )

    fault_supervisor = Node(
        package='coordination',
        executable='fault_supervisor_node',
        name='fault_supervisor',
        namespace='coordination',
        output='screen',
        parameters=[fault_policy_yaml, {'use_sim_time': use_sim_time}],
    )

    task_allocator = Node(
        package='coordination',
        executable='task_allocator_node',
        name='task_allocator',
        namespace='coordination',
        output='screen',
        parameters=[allocator_yaml, {'use_sim_time': use_sim_time}],
    )

    return LaunchDescription([
        use_sim_time_arg,
        mission_manager,
        health_monitor,
        fault_supervisor,
        task_allocator,
    ])
