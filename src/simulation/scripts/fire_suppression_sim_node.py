#!/usr/bin/env python3
from __future__ import annotations

import math
import os
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict, Optional

from ament_index_python.packages import get_package_share_directory
import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node

Incident = getattr(import_module('firescout_interfaces.msg'), 'Incident')


@dataclass(frozen=True)
class FireEntity:
    model_name: str
    light_name: str
    x: float
    y: float


FALLBACK_FIRE_ENTITIES = (
    FireEntity('fire_entity', 'fire_glow_1', 3.0, 2.0),
    FireEntity('fire_2', 'fire_glow_2', 4.02, 5.7862),
    FireEntity('fire_3', 'fire_glow_3', 6.67, -4.54),
    FireEntity('fire_4', 'fire_glow_4', -1.8508, -5.17),
    FireEntity('fire_5', 'fire_glow_5', -7.3638, 0.9669),
    FireEntity('fire_6', 'fire_glow_6', -8.05, -3.31),
    FireEntity('fire_7', 'fire_glow_7', 7.77, -1.80),
)


class FireSuppressionSimNode(Node):
    """Remove Gazebo fire entities once robots reach detected fires."""

    def __init__(self) -> None:
        super().__init__('fire_suppression_sim_node')

        self.declare_parameter('world_name', 'villa_world')
        self.declare_parameter('robot_ids', ['robot1', 'robot2', 'robot3'])
        self.declare_parameter('suppression_radius_m', 2.5)
        self.declare_parameter('fire_match_radius_m', 4.0)
        self.declare_parameter('allow_any_robot_to_suppress', False)
        self.declare_parameter('auto_suppress_on_detection_robot_ids', ['robot1'])
        self.declare_parameter('auto_suppress_on_detection_model_names', ['fire_entity'])
        self.declare_parameter('auto_suppress_when_close_model_names', ['fire_entity'])
        self.declare_parameter('auto_suppress_when_close_radius_m', 5.0)
        self.declare_parameter('gz_timeout_ms', 5000)
        self.declare_parameter('world_sdf_path', '')

        self._world_name = str(self.get_parameter('world_name').value)
        self._fire_entities = self._load_fire_entities()
        robot_ids = list(self.get_parameter('robot_ids').value)
        self._robot_ids = [str(robot_id) for robot_id in robot_ids if str(robot_id)]

        self._latest_odom: Dict[str, Optional[Odometry]] = {
            robot_id: None for robot_id in self._robot_ids
        }
        self._active_incidents: Dict[str, Any] = {}
        self._active_fire_models: set[str] = set()
        self._removed_models: set[str] = set()
        self._removed_lights: set[str] = set()

        for robot_id in self._robot_ids:
            self.create_subscription(
                Odometry,
                f'/{robot_id}/odom',
                self._make_odom_callback(robot_id),
                10,
            )
        self.create_subscription(Incident, '/incidents/fire', self._incident_callback, 10)
        self.create_timer(0.5, self._suppression_timer)

        self.get_logger().info(
            f'Fire suppression sim node watching {len(self._fire_entities)} fire entities '
            f'in world {self._world_name}'
        )

    def _make_odom_callback(self, robot_id: str):
        def _callback(msg: Odometry) -> None:
            self._latest_odom[robot_id] = msg

        return _callback

    def _incident_callback(self, msg: Any) -> None:
        if str(getattr(msg, 'incident_type', '')).upper() != 'FIRE':
            return
        incident_id = str(msg.incident_id)
        if incident_id:
            self._active_incidents[incident_id] = msg
        fire = self._nearest_fire_entity(
            float(msg.position.position.x),
            float(msg.position.position.y),
        )
        if fire is not None:
            self._active_fire_models.add(fire.model_name)
            if self._should_auto_suppress_on_detection(msg, fire):
                self.get_logger().info(
                    f'Fire incident {incident_id} matched {fire.model_name}; '
                    f'auto-suppressing on detection for {msg.robot_id}'
                )
                if self._suppress_fire_entity(fire, incident_id, str(msg.robot_id), 0.0):
                    self._active_incidents.pop(incident_id, None)
                return
            self.get_logger().info(
                f'Fire incident {incident_id} matched {fire.model_name}; '
                f'waiting for robot within suppression radius'
            )
        else:
            self.get_logger().warning(
                f'Fire incident {incident_id} did not match a known fire model; '
                f'position=({msg.position.position.x:.2f}, {msg.position.position.y:.2f})'
            )

    def _suppression_timer(self) -> None:
        suppression_radius = float(self.get_parameter('suppression_radius_m').value)
        allow_any_robot = bool(self.get_parameter('allow_any_robot_to_suppress').value)

        auto_radius = float(
            self.get_parameter('auto_suppress_when_close_radius_m').value
        )
        self._suppress_configured_fires_near_any_robot(auto_radius)

        if allow_any_robot and self._active_incidents:
            self._suppress_any_detected_fire_near_any_robot(suppression_radius)

        for incident_id, incident in list(self._active_incidents.items()):
            robot_id = str(incident.robot_id)
            odom = self._latest_odom.get(robot_id)
            if odom is None:
                continue

            robot_x = float(odom.pose.pose.position.x)
            robot_y = float(odom.pose.pose.position.y)
            fire_x = float(incident.position.position.x)
            fire_y = float(incident.position.position.y)
            distance = math.hypot(fire_x - robot_x, fire_y - robot_y)
            if distance > suppression_radius:
                continue

            fire = self._nearest_fire_entity(fire_x, fire_y)
            if fire is None:
                self.get_logger().warning(
                    f'Incident {incident_id} is near no known fire entity; '
                    f'position=({fire_x:.2f}, {fire_y:.2f})'
                )
                self._active_incidents.pop(incident_id, None)
                continue
            if fire.model_name in self._removed_models:
                self._active_incidents.pop(incident_id, None)
                continue

            if self._suppress_fire_entity(fire, incident_id, robot_id, distance):
                self._active_incidents.pop(incident_id, None)

    def _suppress_any_detected_fire_near_any_robot(self, suppression_radius: float) -> None:
        candidate_models = set(self._active_fire_models)
        if not candidate_models:
            candidate_models = {
                fire.model_name for fire in self._fire_entities
                if fire.model_name not in self._removed_models
            }

        for fire in self._fire_entities:
            if fire.model_name not in candidate_models:
                continue
            if fire.model_name in self._removed_models:
                self._active_fire_models.discard(fire.model_name)
                continue

            closest_robot_id = None
            closest_distance = float('inf')
            for robot_id, odom in self._latest_odom.items():
                if odom is None:
                    continue
                robot_x = float(odom.pose.pose.position.x)
                robot_y = float(odom.pose.pose.position.y)
                distance = math.hypot(fire.x - robot_x, fire.y - robot_y)
                if distance < closest_distance:
                    closest_robot_id = robot_id
                    closest_distance = distance

            if closest_robot_id is None or closest_distance > suppression_radius:
                continue

            self.get_logger().info(
                f'{closest_robot_id} is {closest_distance:.2f}m from {fire.model_name}; '
                'requesting Gazebo removal'
            )
            self._suppress_fire_entity(
                fire,
                incident_id='detected_fire',
                robot_id=closest_robot_id,
                distance=closest_distance,
            )

    def _suppress_configured_fires_near_any_robot(self, suppression_radius: float) -> None:
        model_names = {
            str(model_name)
            for model_name in self.get_parameter(
                'auto_suppress_when_close_model_names'
            ).value
        }
        if not model_names:
            return

        for fire in self._fire_entities:
            if fire.model_name not in model_names:
                continue
            if fire.model_name in self._removed_models:
                continue

            closest_robot_id = None
            closest_distance = float('inf')
            for robot_id, odom in self._latest_odom.items():
                if odom is None:
                    continue
                robot_x = float(odom.pose.pose.position.x)
                robot_y = float(odom.pose.pose.position.y)
                distance = math.hypot(fire.x - robot_x, fire.y - robot_y)
                if distance < closest_distance:
                    closest_robot_id = robot_id
                    closest_distance = distance

            if closest_robot_id is None or closest_distance > suppression_radius:
                continue

            self.get_logger().info(
                f'{closest_robot_id} is {closest_distance:.2f}m from {fire.model_name}; '
                'auto-suppressing because robot is close'
            )
            self._suppress_fire_entity(
                fire,
                incident_id='proximity',
                robot_id=closest_robot_id,
                distance=closest_distance,
            )

    def _should_auto_suppress_on_detection(self, incident: Any, fire: FireEntity) -> bool:
        robot_ids = {
            str(robot_id)
            for robot_id in self.get_parameter(
                'auto_suppress_on_detection_robot_ids'
            ).value
        }
        model_names = {
            str(model_name)
            for model_name in self.get_parameter(
                'auto_suppress_on_detection_model_names'
            ).value
        }
        return str(incident.robot_id) in robot_ids and fire.model_name in model_names

    def _suppress_fire_entity(
        self,
        fire: FireEntity,
        incident_id: str,
        robot_id: str,
        distance: float,
    ) -> bool:
        if fire.model_name in self._removed_models:
            self._active_fire_models.discard(fire.model_name)
            return True

        if self._remove_entity(fire.model_name, entity_type='MODEL'):
            self._removed_models.add(fire.model_name)
            self._active_fire_models.discard(fire.model_name)
            self.get_logger().info(
                f'Suppressed {fire.model_name} for incident {incident_id}; '
                f'{robot_id} distance={distance:.2f}m'
            )
            self._remove_light(fire)
            return True
        return False

    def _nearest_fire_entity(self, x: float, y: float) -> Optional[FireEntity]:
        match_radius = float(self.get_parameter('fire_match_radius_m').value)
        nearest = None
        nearest_distance = float('inf')
        for fire in self._fire_entities:
            distance = math.hypot(fire.x - x, fire.y - y)
            if distance < nearest_distance:
                nearest = fire
                nearest_distance = distance
        if nearest is None:
            return None
        if nearest_distance > match_radius:
            self.get_logger().warning(
                f'Nearest Gazebo fire model to detection is {nearest.model_name} '
                f'at {nearest_distance:.2f}m, outside match radius {match_radius:.2f}m'
            )
            return None
        return nearest

    def _remove_light(self, fire: FireEntity) -> None:
        if not fire.light_name:
            return
        if fire.light_name in self._removed_lights:
            return
        if self._remove_entity(fire.light_name, entity_type='LIGHT'):
            self._removed_lights.add(fire.light_name)

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

    def _load_fire_entities(self) -> tuple[FireEntity, ...]:
        world_path = str(self.get_parameter('world_sdf_path').value)
        if not world_path:
            world_path = os.path.join(
                get_package_share_directory('simulation'),
                'worlds',
                'world_1.sdf',
            )

        try:
            root = ET.parse(world_path).getroot()
        except (OSError, ET.ParseError) as exc:
            self.get_logger().warning(
                f'Could not read fire entities from {world_path}: {exc}; '
                'using fallback fire coordinates'
            )
            return FALLBACK_FIRE_ENTITIES

        models = []
        lights = []
        world = root.find('world')
        if world is None:
            return FALLBACK_FIRE_ENTITIES

        for model in world.findall('model'):
            name = str(model.attrib.get('name', ''))
            if not (name == 'fire_entity' or name.startswith('fire_')):
                continue
            pose = self._pose_xy(model.findtext('pose'))
            if pose is not None:
                models.append((name, pose[0], pose[1]))

        for light in world.findall('light'):
            name = str(light.attrib.get('name', ''))
            if not name.startswith('fire_glow_'):
                continue
            pose = self._pose_xy(light.findtext('pose'))
            if pose is not None:
                lights.append((name, pose[0], pose[1]))

        entities = []
        for model_name, x, y in models:
            light_name = self._nearest_light_name(x, y, lights)
            entities.append(FireEntity(model_name, light_name, x, y))

        if not entities:
            return FALLBACK_FIRE_ENTITIES

        self.get_logger().info(
            f'Loaded fire positions from {world_path}: ' +
            ', '.join(f'{fire.model_name}=({fire.x:.2f},{fire.y:.2f})' for fire in entities)
        )
        return tuple(entities)

    @staticmethod
    def _pose_xy(pose_text: Optional[str]) -> Optional[tuple[float, float]]:
        if not pose_text:
            return None
        parts = pose_text.split()
        if len(parts) < 2:
            return None
        try:
            return float(parts[0]), float(parts[1])
        except ValueError:
            return None

    @staticmethod
    def _nearest_light_name(
        x: float,
        y: float,
        lights: list[tuple[str, float, float]],
    ) -> str:
        if not lights:
            return ''
        return min(lights, key=lambda item: math.hypot(item[1] - x, item[2] - y))[0]


def main(args=None) -> None:
    rclpy.init(args=args)
    node = FireSuppressionSimNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
