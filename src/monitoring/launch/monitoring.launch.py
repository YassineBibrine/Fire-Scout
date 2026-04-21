from launch import LaunchDescription
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Launch all monitoring nodes in /monitoring namespace with shared configs."""
    monitor_topics_yaml = [FindPackageShare('monitoring'), '/config/monitor_topics.yaml']
    thresholds_yaml = [FindPackageShare('monitoring'), '/config/thresholds.yaml']

    common_parameters = [monitor_topics_yaml, thresholds_yaml]

    # NOTE: Monitoring nodes commented out due to ROS 2 launcher executable discovery issue.
    # The executables work via CLI but not through ros2 launch.
    # Workaround: Run directly from command line - source install/setup.bash && topic_rate_monitor
    # TODO: Fix entry point registration in setup.py or use alternative launch mechanism
    
    # topic_rate_monitor = Node(
    #     package='monitoring',
    #     executable='topic_rate_monitor',
    #     name='topic_rate_monitor_node',
    #     namespace='monitoring',
    #     output='screen',
    #     parameters=common_parameters,
    # )

    # latency_monitor = Node(
    #     package='monitoring',
    #     executable='latency_monitor',
    #     name='latency_monitor_node',
    #     namespace='monitoring',
    #     output='screen',
    #     parameters=common_parameters,
    # )

    # metrics_exporter = Node(
    #     package='monitoring',
    #     executable='metrics_exporter',
    #     name='metrics_exporter_node',
    #     namespace='monitoring',
    #     output='screen',
    #     parameters=common_parameters,
    # )

    return LaunchDescription([
        # topic_rate_monitor,
        # latency_monitor,
        # metrics_exporter,
    ])
