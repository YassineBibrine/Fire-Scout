from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Launch all monitoring nodes in /monitoring namespace with shared configs."""
    use_sim_time = LaunchConfiguration('use_sim_time')

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulated clock time.',
    )

    monitor_topics_yaml = [FindPackageShare('monitoring'), '/config/monitor_topics.yaml']
    thresholds_yaml = [FindPackageShare('monitoring'), '/config/thresholds.yaml']

    common_parameters = [monitor_topics_yaml, thresholds_yaml]

    topic_rate_monitor = Node(
        package='monitoring',
        executable='topic_rate_monitor',
        name='topic_rate_monitor_node',
        namespace='monitoring',
        output='screen',
        parameters=common_parameters + [{'use_sim_time': use_sim_time}],
    )

    latency_monitor = Node(
        package='monitoring',
        executable='latency_monitor',
        name='latency_monitor_node',
        namespace='monitoring',
        output='screen',
        parameters=common_parameters + [{'use_sim_time': use_sim_time}],
    )

    metrics_exporter = Node(
        package='monitoring',
        executable='metrics_exporter',
        name='metrics_exporter_node',
        namespace='monitoring',
        output='screen',
        parameters=common_parameters + [{'use_sim_time': use_sim_time}],
    )

    return LaunchDescription([
        use_sim_time_arg,
        topic_rate_monitor,
        latency_monitor,
        metrics_exporter,
    ])
