from importlib import import_module
import uuid

import rclpy
from rclpy.node import Node

# Resolve the generated ROS message classes dynamically to avoid static analyzer
# false positives when interface stubs are not discoverable in the IDE env.
FaultEvent = getattr(import_module('firescout_interfaces.msg'), 'FaultEvent')
NodeStatus = getattr(import_module('firescout_interfaces.msg'), 'NodeStatus')
MissionState = getattr(import_module('firescout_interfaces.msg'), 'MissionState')
ReportFault = getattr(import_module('firescout_interfaces.srv'), 'ReportFault')


class FaultSupervisorNode(Node):

    def __init__(self):

        super().__init__('fault_supervisor_node')

        self.declare_parameter(
            'heartbeat_timeout_sec',
            2.0
        )

        if not self.has_parameter('use_sim_time'):
            self.declare_parameter(
                'use_sim_time',
                True
            )

        self.heartbeat_timeout_sec = self.get_parameter(
            'heartbeat_timeout_sec'
        ).value

        self.declare_parameter('robot_ids', ['robot1', 'robot2', 'robot3'])
        robot_ids = list(self.get_parameter('robot_ids').value)
        self.robots = [str(robot) for robot in robot_ids if str(robot)] or ['robot1', 'robot2', 'robot3']
        self._last_degraded_set = set()

        self.report_fault_service = self.create_service(
            ReportFault,
            '/coordination/services/report_fault',
            self.report_fault_service_callback
        )

        self.create_subscription(
            FaultEvent,
            '/coordination/fault_events',
            self.fault_event_callback,
            10
        )

        self.create_subscription(
            NodeStatus,
            '/coordination/system_health',
            self.system_health_callback,
            10
        )

        self.mission_state_pub = self.create_publisher(
            MissionState,
            '/mission/state',
            10
        )

        self.get_logger().info(
            'Fault Supervisor Node started'
        )

    def fault_event_callback(self, event):

        self.get_logger().error(
            f"Fault from {event.robot_id}: {event.fault_type} severity={event.severity}"
        )

        request_robot_id = event.robot_id
        fault_type = event.fault_type
        severity = event.severity

        fault_id = str(uuid.uuid4())
        self.get_logger().info(
            f"Fault logged: {request_robot_id} {fault_type} severity={severity} "
            f"id={fault_id}"
        )

    def system_health_callback(self, status):

        if status.status != 'DEGRADED':
            return

        degraded = []
        if status.error_message:
            degraded = [
                robot.strip()
                for robot in status.error_message.split(',')
                if robot.strip()
            ]
        degraded_set = set(degraded)

        if degraded_set != self._last_degraded_set:
            self.get_logger().warning(
                f"System degraded: {status.error_message} - fault supervisor active"
            )
            self._last_degraded_set = degraded_set

        active_robots = [
            robot
            for robot in self.robots
            if robot not in degraded
        ]

        mission_state = MissionState()
        mission_state.mission_id = 'auto'
        mission_state.state = 'DEGRADED'
        mission_state.active_robots = active_robots
        mission_state.mission_progress = 0.0
        mission_state.timestamp = (
            self.get_clock()
            .now()
            .to_msg()
        )

        self.mission_state_pub.publish(mission_state)

    def report_fault_service_callback(self, request, response):

        self.get_logger().info(
            f"Fault reported from {request.robot_id}: {request.fault_type} severity={request.severity}"
        )

        response.logged = True
        response.fault_id = str(uuid.uuid4())

        return response


def main(args=None):

    rclpy.init(args=args)

    node = FaultSupervisorNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
