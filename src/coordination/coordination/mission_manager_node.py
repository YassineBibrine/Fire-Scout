from importlib import import_module

import rclpy
from rclpy.node import Node

# Resolve the generated ROS message classes dynamically to avoid static analyzer
# false positives when interface stubs are not discoverable in the IDE env.
MissionState = getattr(import_module('firescout_interfaces.msg'), 'MissionState')
Incident = getattr(import_module('firescout_interfaces.msg'), 'Incident')
NodeStatus = getattr(import_module('firescout_interfaces.msg'), 'NodeStatus')


class MissionManagerNode(Node):

    def __init__(self):

        super().__init__('mission_manager_node')

        if not self.has_parameter('use_sim_time'):
            self.declare_parameter(
                'use_sim_time',
                True
            )

        self.current_state = 'INIT'
        self.start_time = self.get_clock().now()
        self.last_incident_time = None
        self.last_incident = None
        self.degraded_override = False

        self.robots = ['robot1', 'robot2', 'robot3']

        self.create_subscription(
            MissionState,
            '/mission/state',
            self.mission_state_callback,
            10
        )

        self.create_subscription(
            Incident,
            '/incidents/fire',
            self.incident_callback,
            10
        )

        self.create_subscription(
            Incident,
            '/incidents/human',
            self.incident_callback,
            10
        )

        self.create_subscription(
            NodeStatus,
            '/coordination/system_health',
            self.system_health_callback,
            10
        )

        self.publisher_ = self.create_publisher(
            MissionState,
            '/mission/state',
            10
        )

        self.timer = self.create_timer(
            2.0,
            self.publish_state
        )

        self.get_logger().info(
            'Mission Manager Node started'
        )

    def mission_state_callback(self, _msg):

        return

    def incident_callback(self, incident):

        if incident.priority <= 0.5:
            return

        self.last_incident = incident
        self.last_incident_time = self.get_clock().now()
        if not self.degraded_override:
            self.current_state = 'RESPONDING'

    def system_health_callback(self, status):

        if status.status == 'DEGRADED':
            self.degraded_override = True
            self.current_state = 'DEGRADED'
            return

        if self.degraded_override and status.status == 'HEALTHY':
            self.degraded_override = False
            self.current_state = 'EXPLORING'

    def publish_state(self):

        now = self.get_clock().now()

        if self.current_state == 'INIT':
            elapsed = (now - self.start_time).nanoseconds / 1e9
            if elapsed >= 3.0:
                self.current_state = 'EXPLORING'

        if self.current_state == 'RESPONDING' and self.last_incident_time is not None:
            idle_time = (now - self.last_incident_time).nanoseconds / 1e9
            if idle_time >= 10.0:
                self.current_state = 'EXPLORING'

        mission_state = MissionState()
        mission_state.mission_id = 'main_mission'
        mission_state.state = self.current_state
        mission_state.active_robots = list(self.robots)
        mission_state.timestamp = now.to_msg()

        elapsed = (now - self.start_time).nanoseconds / 1e9
        total = max(elapsed, 1.0)
        mission_state.mission_progress = min(elapsed / total, 1.0)

        self.publisher_.publish(mission_state)


def main(args=None):

    rclpy.init(args=args)

    node = MissionManagerNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
