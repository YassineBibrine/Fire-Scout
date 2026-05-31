from importlib import import_module
from typing import Any

import rclpy
from rclpy.node import Node

FireDetection = getattr(import_module('firescout_interfaces.msg'), 'FireDetection')
Incident = getattr(import_module('firescout_interfaces.msg'), 'Incident')

# ---------------------------------------------------------------------------
# Priority model  (shared with rescue_planning_node)
# ---------------------------------------------------------------------------
# Human incidents always outrank fire incidents.
# Within fire incidents: higher confidence wins, robot1 > robot2 > robot3.

_PRIORITY_HUMAN_BASE = 10.0
_PRIORITY_FIRE_BASE = 5.0

_ROBOT_OFFSET = {
    'robot1': 0.003,
    'robot2': 0.002,
    'robot3': 0.001,
}
_DEFAULT_ROBOT_OFFSET = 0.0


def compute_incident_priority(
    incident_type: str, confidence: float, robot_id: str
) -> float:
    """Return float priority; higher = more urgent."""
    if incident_type == 'human':
        base = _PRIORITY_HUMAN_BASE
    elif incident_type == 'fire':
        base = _PRIORITY_FIRE_BASE
    else:
        base = 0.0
    robot_offset = _ROBOT_OFFSET.get(robot_id, _DEFAULT_ROBOT_OFFSET)
    return base + confidence + robot_offset


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------


class SuppressionPlanningNode(Node):
    """
    Converts hybrid-confirmed FireDetection messages (which are only
    emitted after 2-of-2 sensor+camera fusion) into Incident messages
    published on the global /incidents/fire topic.  Priority is computed
    using the shared conflict-resolution model.

    Phase 2 note: because FireDetectionNode now gates on FusionDecision,
    every FireDetection arriving here has already passed the 2-of-2 check.
    The confidence filter below is a secondary quality gate only.

    Subscribes : /{robot_id}/fire_detection  (FireDetection)
    Publishes  : /incidents/fire             (Incident)
    """

    def __init__(self):
        super().__init__('suppression_planning_node')

        self.declare_parameter('robot_id', 'robot1')
        if not self.has_parameter('use_sim_time'):
            self.declare_parameter('use_sim_time', True)

        self.robot_id: str = self.get_parameter('robot_id').value
        self.seq = 0

        self.subscription = self.create_subscription(
            FireDetection,
            f'/{self.robot_id}/fire_detection',
            self.fire_detection_callback,
            10,
        )

        self.publisher_ = self.create_publisher(
            Incident,
            '/incidents/fire',
            10,
        )

        self.get_logger().info(
            f'SuppressionPlanningNode started for {self.robot_id}'
        )

    def fire_detection_callback(self, detection: Any) -> None:
        # Secondary confidence gate (primary gate is inside FireDetectionNode)
        if detection.confidence <= 0.7:
            return

        position = getattr(detection, 'position', None)
        if position is None:
            self.get_logger().warn(
                'Fire detection missing position; ignoring message'
            )
            return

        self.seq += 1
        incident_id = f'fire_{self.robot_id}_{self.seq}'

        incident = Incident()
        incident.incident_id = incident_id
        incident.incident_type = 'FIRE'
        incident.robot_id = self.robot_id
        incident.position = position
        incident.priority = compute_incident_priority(
            'fire', detection.confidence, self.robot_id
        )
        incident.detection_time = self.get_clock().now().to_msg()
        incident.last_updated = incident.detection_time

        self.publisher_.publish(incident)
        self.get_logger().info(
            f'Suppression incident published: id={incident_id} '
            f'confidence={detection.confidence:.2f} '
            f'priority={incident.priority:.3f}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = SuppressionPlanningNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
