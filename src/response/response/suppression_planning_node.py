import math
import subprocess
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Optional

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


@dataclass(frozen=True)
class FireEntity:
    model_name: str
    light_name: str
    x: float
    y: float


FIRE_ENTITIES = (
    FireEntity('fire_entity', 'fire_glow_1', 3.0, 2.0),
    FireEntity('fire_2', 'fire_glow_2', 4.02, 5.7862),
    FireEntity('fire_3', 'fire_glow_3', 6.67, -4.54),
    FireEntity('fire_4', 'fire_glow_4', -1.8508, -5.17),
    FireEntity('fire_5', 'fire_glow_5', -7.3638, 0.9669),
    FireEntity('fire_6', 'fire_glow_6', -8.05, -3.31),
    FireEntity('fire_7', 'fire_glow_7', 7.77, -1.80),
)


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
        self.declare_parameter('remove_fire_entity_on_detection', False)
        self.declare_parameter('world_name', 'villa_world')
        self.declare_parameter('fire_match_radius_m', 4.0)
        self.declare_parameter('gz_timeout_ms', 5000)
        if not self.has_parameter('use_sim_time'):
            self.declare_parameter('use_sim_time', True)

        self.robot_id: str = self.get_parameter('robot_id').value
        self._world_name = str(self.get_parameter('world_name').value)
        self._removed_fire_models: set[str] = set()
        self._removed_fire_lights: set[str] = set()
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
        # Upstream FireDetectionNode only emits confirmed fusion fires.
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
        if bool(self.get_parameter('remove_fire_entity_on_detection').value):
            self._remove_nearest_fire_entity(position, incident_id)

    def _remove_nearest_fire_entity(self, position: Any, incident_id: str) -> None:
        fire = self._nearest_fire_entity(
            float(position.position.x),
            float(position.position.y),
        )
        if fire is None:
            self.get_logger().warning(
                f'Incident {incident_id} did not match a known Gazebo fire model; '
                f'position=({position.position.x:.2f}, {position.position.y:.2f})'
            )
            return

        self.get_logger().info(
            f'Suppression incident {incident_id} matched {fire.model_name}; '
            'removing Gazebo fire model'
        )
        if self._remove_entity(fire.model_name, entity_type='MODEL'):
            self._removed_fire_models.add(fire.model_name)
            self.get_logger().info(
                f'Suppressed Gazebo fire model {fire.model_name} for {incident_id}'
            )
            if fire.light_name not in self._removed_fire_lights:
                if self._remove_entity(fire.light_name, entity_type='LIGHT'):
                    self._removed_fire_lights.add(fire.light_name)

    def _nearest_fire_entity(self, x: float, y: float) -> Optional[FireEntity]:
        match_radius = float(self.get_parameter('fire_match_radius_m').value)
        nearest = None
        nearest_distance = float('inf')
        for fire in FIRE_ENTITIES:
            distance = math.hypot(fire.x - x, fire.y - y)
            if distance < nearest_distance:
                nearest = fire
                nearest_distance = distance

        if nearest is None or nearest_distance > match_radius:
            if nearest is not None:
                self.get_logger().warning(
                    f'Nearest Gazebo fire model to detection is {nearest.model_name} '
                    f'at {nearest_distance:.2f}m, outside match radius {match_radius:.2f}m'
                )
            return None
        return nearest

    def _remove_entity(self, name: str, entity_type: str) -> bool:
        timeout_ms = int(self.get_parameter('gz_timeout_ms').value)
        entity_type_value = 2 if entity_type == 'MODEL' else 1
        world_names = [self._world_name]
        if self._world_name != 'default':
            world_names.append('default')

        for world_name in world_names:
            service = f'/world/{world_name}/remove'
            cmd = [
                'gz',
                'service',
                '-s',
                service,
                '--reqtype',
                'gz.msgs.Entity',
                '--reptype',
                'gz.msgs.Boolean',
                '--timeout',
                str(timeout_ms),
                '--req',
                f'name: "{name}" type: {entity_type_value}',
            ]
            self.get_logger().info(
                f'Removing Gazebo {entity_type.lower()} {name} via {service}'
            )
            try:
                result = subprocess.run(
                    cmd,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=max(8.0, timeout_ms / 1000.0 + 2.0),
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                self.get_logger().warning(
                    f'Failed to call Gazebo remove service {service} for {name}: {exc}'
                )
                continue

            output = f'{result.stdout}\n{result.stderr}'.strip()
            if result.returncode == 0 and ('data: true' in output or 'true' in output.lower()):
                return True

            self.get_logger().warning(
                f'Gazebo remove service {service} did not confirm removal of {name}; '
                f'returncode={result.returncode} output={output}'
            )
        return False


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
