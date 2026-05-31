from importlib import import_module

import rclpy
from rclpy.duration import Duration
from rclpy.node import Node

Incident = getattr(import_module('firescout_interfaces.msg'), 'Incident')
TaskAssignment = getattr(import_module('firescout_interfaces.msg'), 'TaskAssignment')

_FIRE_DEADLINE_SEC = 30.0
_HUMAN_DEADLINE_SEC = 20.0

_TASK_TYPE_FIRE = 'SUPPRESS'
_TASK_TYPE_HUMAN = 'RESCUE'


class CoordinationBridgeNode(Node):
    """
    Bridges confirmed incidents from the response pipeline to the coordination
    layer by publishing TaskAssignment messages on /coordination/task_assignments.

    This closes the spec requirement: "hybrid-confirmed incidents trigger
    actionable TaskAssignment outputs with bounded response latency."

    Subscribes : /incidents/fire   (Incident)
                 /incidents/human  (Incident)
    Publishes  : /coordination/task_assignments  (TaskAssignment)
    """

    def __init__(self):
        super().__init__('coordination_bridge_node')

        self.declare_parameter('robot_id', 'robot1')
        if not self.has_parameter('use_sim_time'):
            self.declare_parameter('use_sim_time', False)

        self.robot_id: str = self.get_parameter('robot_id').value

        self._pub = self.create_publisher(
            TaskAssignment,
            '/coordination/task_assignments',
            10,
        )

        self._fire_sub = self.create_subscription(
            Incident,
            '/incidents/fire',
            self._fire_cb,
            10,
        )
        self._human_sub = self.create_subscription(
            Incident,
            '/incidents/human',
            self._human_cb,
            10,
        )

        self.get_logger().info('CoordinationBridgeNode started')

    def _fire_cb(self, msg: Incident) -> None:
        assignment = self._build_assignment(msg, _TASK_TYPE_FIRE, _FIRE_DEADLINE_SEC)
        self._pub.publish(assignment)
        self.get_logger().info(
            f'TaskAssignment published: type=SUPPRESS robot={msg.robot_id} '
            f'incident={msg.incident_id} priority={msg.priority:.3f}'
        )

    def _human_cb(self, msg: Incident) -> None:
        assignment = self._build_assignment(msg, _TASK_TYPE_HUMAN, _HUMAN_DEADLINE_SEC)
        self._pub.publish(assignment)
        self.get_logger().info(
            f'TaskAssignment published: type=RESCUE robot={msg.robot_id} '
            f'incident={msg.incident_id} priority={msg.priority:.3f}'
        )

    def _build_assignment(self, incident: Incident, task_type: str, deadline_sec: float) -> TaskAssignment:
        now = self.get_clock().now()
        assignment = TaskAssignment()
        assignment.task_id = incident.incident_id
        assignment.task_type = task_type
        assignment.assigned_robot = incident.robot_id
        assignment.target_pose = incident.position
        assignment.priority = incident.priority
        assignment.estimated_duration = 0.0
        assignment.assignment_time = now.to_msg()
        assignment.deadline = (now + Duration(seconds=deadline_sec)).to_msg()
        return assignment


def main(args=None):
    rclpy.init(args=args)
    node = CoordinationBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
