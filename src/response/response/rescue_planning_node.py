from importlib import import_module
from typing import Any

import rclpy
from rclpy.node import Node

HumanDetection = getattr(import_module('firescout_interfaces.msg'), 'HumanDetection')
Incident = getattr(import_module('firescout_interfaces.msg'), 'Incident')

# ---------------------------------------------------------------------------
# Priority model
# ---------------------------------------------------------------------------
# Rule 1 – incident type:   HUMAN > FIRE  (base offsets 10.0 vs 5.0)
# Rule 2 – confidence:      higher wins within same type
# Rule 3 – robot tiebreak:  robot1 > robot2 > robot3 (small deterministic offsets)
#
# Example outcomes:
#   Human(0.51) priority = 10.0 + 0.51 + offset  ≈ 10.513
#   Fire(0.99)  priority =  5.0 + 0.99 + offset   ≈  5.993
#   → Human(0.51) > Fire(0.99)  ✓
#
#   Human(0.90, robot1) = 10.903   > Human(0.80, robot1) = 10.803  ✓
#   Human(0.70, robot1) = 10.703   > Human(0.70, robot2) = 10.702  ✓

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
    """
    Return a float priority for the incident.  Higher = more urgent.
    Human incidents always outrank fire incidents regardless of confidence.
    """
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


class RescuePlanningNode(Node):
    """
    Converts confirmed HumanDetection messages into Incident messages
    published on the global /incidents/human topic.  Priority is computed
    using the shared conflict-resolution model so that the mission manager
    and task allocator can rank all active incidents consistently.

    Subscribes : /{robot_id}/human_detection  (HumanDetection)
    Publishes  : /incidents/human             (Incident)
    """

    def __init__(self):
        super().__init__('rescue_planning_node')

        self.declare_parameter('robot_id', 'robot1')
        if not self.has_parameter('use_sim_time'):
            self.declare_parameter('use_sim_time', True)

        self.robot_id: str = self.get_parameter('robot_id').value
        self.seq = 0

        self.subscription = self.create_subscription(
            HumanDetection,
            f'/{self.robot_id}/human_detection',
            self.human_detection_callback,
            10,
        )

        self.publisher_ = self.create_publisher(
            Incident,
            '/incidents/human',
            10,
        )

        self.get_logger().info(
            f'RescuePlanningNode started for {self.robot_id}'
        )

    def human_detection_callback(self, detection: Any) -> None:
        if not detection.needs_rescue:
            return
        # Upstream HumanDetectionNode already gates on human_confidence_threshold.

        position = getattr(detection, 'position', None)
        if position is None:
            self.get_logger().warn(
                'Human detection missing position; ignoring message'
            )
            return

        self.seq += 1
        incident_id = f'rescue_{self.robot_id}_{self.seq}'

        incident = Incident()
        incident.incident_id = incident_id
        incident.incident_type = 'HUMAN'
        incident.robot_id = self.robot_id
        incident.position = position
        incident.priority = compute_incident_priority(
            'human', detection.confidence, self.robot_id
        )
        incident.detection_time = self.get_clock().now().to_msg()
        incident.last_updated = incident.detection_time

        self.publisher_.publish(incident)
        self.get_logger().info(
            f'Rescue incident published: id={incident_id} '
            f'confidence={detection.confidence:.2f} '
            f'priority={incident.priority:.3f}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = RescuePlanningNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
