import math
from importlib import import_module
from typing import Any, Optional

import rclpy
from geometry_msgs.msg import Pose
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener

FireSensorAlert = getattr(import_module('firescout_interfaces.msg'), 'FireSensorAlert')
VisionDetectionArray = getattr(
    import_module('firescout_interfaces.msg'), 'VisionDetectionArray'
)
FusionDecision = getattr(import_module('firescout_interfaces.msg'), 'FusionDecision')

_NS_PER_SEC = 1_000_000_000


class FusionDecisionNode(Node):
    """
    Hybrid 2-of-2 sensor fusion.

    A fire incident is confirmed ONLY when BOTH the physical sensor alert
    AND a camera detection agree within `confirmation_window_sec` seconds.
    A human incident is confirmed by camera vision alone.

    Subscribes : /{robot_id}/fire_sensor_alert   (FireSensorAlert)
                 /{robot_id}/camera_detections    (VisionDetectionArray)
    Publishes  : /{robot_id}/fusion_decision      (FusionDecision)

    Parameters:
        robot_id                   – robot namespace (default: robot1)
        confirmation_window_sec    – max age / temporal gap (default: 3.0 s)
        fire_sensor_threshold      – min normalized_risk for sensor fire (0.5)
        vision_confidence_threshold– min per-detection confidence     (0.4)
        confirmed_cooldown_sec     – duplicate suppression window      (1.0 s)
    """

    def __init__(self):
        super().__init__('fusion_decision_node')

        self.declare_parameter('robot_id', 'robot1')
        self.declare_parameter('confirmation_window_sec', 3.0)
        self.declare_parameter('fire_sensor_threshold', 0.5)
        self.declare_parameter('vision_confidence_threshold', 0.4)
        self.declare_parameter('confirmed_cooldown_sec', 1.0)
        self.declare_parameter('publish_rate_hz', 2.0)
        if not self.has_parameter('use_sim_time'):
            self.declare_parameter('use_sim_time', False)

        self.robot_id: str = self.get_parameter('robot_id').value
        self._window_sec: float = (
            self.get_parameter('confirmation_window_sec').value
        )
        self._sensor_thr: float = (
            self.get_parameter('fire_sensor_threshold').value
        )
        self._vision_thr: float = (
            self.get_parameter('vision_confidence_threshold').value
        )
        self._cooldown_sec: float = (
            self.get_parameter('confirmed_cooldown_sec').value
        )
        self._publish_rate_hz = max(
            float(self.get_parameter('publish_rate_hz').value),
            0.1,
        )

        self._latest_sensor: Optional[Any] = None
        self._latest_vision: Optional[Any] = None
        self._last_confirmed: Time | None = None
        self._tf_buffer = Buffer()
        self._tf_listener = TransformListener(self._tf_buffer, self)

        reliable_depth_5 = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=5,
            reliability=ReliabilityPolicy.RELIABLE,
        )
        camera_depth_1 = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.BEST_EFFORT,
        )
        self._sensor_sub = self.create_subscription(
            FireSensorAlert,
            f'/{self.robot_id}/fire_sensor_alert',
            self._sensor_cb,
            reliable_depth_5,
        )
        self._vision_sub = self.create_subscription(
            VisionDetectionArray,
            f'/{self.robot_id}/camera_detections',
            self._vision_cb,
            camera_depth_1,
        )
        self._pub = self.create_publisher(
            FusionDecision,
            f'/{self.robot_id}/fusion_decision',
            reliable_depth_5,
        )
        self.create_timer(1.0 / self._publish_rate_hz, self._publish_decision)

        self.get_logger().info(
            f'FusionDecisionNode started for {self.robot_id} '
            f'window={self._window_sec}s sensor_thr={self._sensor_thr} '
            f'vision_thr={self._vision_thr}'
        )

    # ------------------------------------------------------------------
    # Subscription callbacks
    # ------------------------------------------------------------------

    def _sensor_cb(self, msg: Any) -> None:
        self._latest_sensor = msg

    def _vision_cb(self, msg: Any) -> None:
        self._latest_vision = msg

    # ------------------------------------------------------------------
    # Fusion logic
    # ------------------------------------------------------------------

    def _publish_decision(self) -> None:
        now = self.get_clock().now()
        sensor = self._latest_sensor
        vision = self._latest_vision

        sensor_fresh = False
        vision_fresh = False
        temporal_gap_ok = False
        sensor_time: Optional[Time] = None
        vision_time: Optional[Time] = None
        if sensor is not None:
            sensor_time = Time.from_msg(sensor.timestamp)
            sensor_age = (now - sensor_time).nanoseconds / _NS_PER_SEC
            sensor_fresh = 0.0 <= sensor_age <= self._window_sec
        if vision is not None:
            vision_time = Time.from_msg(vision.timestamp)
            vision_age = (now - vision_time).nanoseconds / _NS_PER_SEC
            vision_fresh = 0.0 <= vision_age <= self._window_sec
        if (
            sensor_fresh
            and vision_fresh
            and sensor_time is not None
            and vision_time is not None
        ):
            temporal_gap = abs(
                (sensor_time - vision_time).nanoseconds
            ) / _NS_PER_SEC
            temporal_gap_ok = temporal_gap <= self._window_sec

        # --- Sensor evaluation ---------------------------------------
        sensor_fire = (
            sensor_fresh
            and sensor is not None
            and (
                sensor.flame_detected
                or sensor.normalized_risk >= self._sensor_thr
            )
        )
        sensor_conf = float(sensor.normalized_risk) if sensor_fresh and sensor else 0.0

        # --- Vision evaluation ---------------------------------------
        fire_dets = [
            d for d in vision.detections
            if d.class_label in ('fire', 'smoke')
            and d.confidence >= self._vision_thr
        ] if vision_fresh and vision else []
        human_dets = [
            d for d in vision.detections
            if d.class_label == 'human'
            and d.confidence >= self._vision_thr
        ] if vision_fresh and vision else []
        vision_fire = len(fire_dets) > 0
        vision_conf = max(
            (d.confidence for d in fire_dets), default=0.0
        )

        # --- 2-of-2 fire confirmation --------------------------------
        fire_confirmed = sensor_fire and vision_fire and temporal_gap_ok

        # --- Human confirmed by vision alone -------------------------
        human_confirmed = len(human_dets) > 0

        # --- Duplicate suppression -----------------------------------
        if (fire_confirmed or human_confirmed) and self._last_confirmed is not None:
            elapsed = (now - self._last_confirmed).nanoseconds / _NS_PER_SEC
            if elapsed < self._cooldown_sec:
                fire_confirmed = False
                human_confirmed = False
            else:
                self._last_confirmed = now
        elif fire_confirmed or human_confirmed:
            self._last_confirmed = now

        # --- Build decision ------------------------------------------
        incident_position = Pose()
        if human_confirmed:
            best_human = max(human_dets, key=lambda d: d.confidence)
            risk = float(best_human.confidence) * 0.7
            action = 'RESCUE'
            out_vision_conf = float(best_human.confidence)
            incident_position = self._pose_to_map(best_human.estimated_pose)
            if incident_position is None:
                fire_confirmed = False
                human_confirmed = False
                risk = 0.0
                action = 'NONE'
                out_vision_conf = vision_conf
                incident_position = Pose()
        elif fire_confirmed:
            best_fire = max(fire_dets, key=lambda d: d.confidence)
            risk = (sensor_conf + vision_conf) / 2.0
            action = 'SUPPRESS'
            out_vision_conf = vision_conf
            incident_position = self._pose_to_map(best_fire.estimated_pose)
            if incident_position is None:
                fire_confirmed = False
                human_confirmed = False
                risk = 0.0
                action = 'NONE'
                incident_position = Pose()
        else:
            risk = 0.0
            action = 'NONE'
            out_vision_conf = vision_conf

        sources = []
        if sensor_fire and sensor is not None:
            sources.append(f'sensor:{sensor.source_id}')
        if (vision_fire or human_confirmed) and vision is not None:
            sources.append(f'camera:{vision.camera_id}')

        decision = FusionDecision()
        decision.robot_id = self.robot_id
        decision.fire_confirmed = fire_confirmed
        decision.human_confirmed = human_confirmed
        decision.risk_level = float(risk)
        decision.recommended_action = action
        decision.contributing_sources = sources
        decision.sensor_confidence = float(sensor_conf)
        decision.vision_confidence = float(out_vision_conf)
        decision.incident_position = incident_position
        decision.timestamp = now.to_msg()

        self._pub.publish(decision)
        self.get_logger().info(
            f'FusionDecision: fire={fire_confirmed} human={human_confirmed} '
            f'risk={risk:.2f} action={action}'
        )

    def _pose_to_map(self, pose: Pose) -> Pose | None:
        """Transform a robot-relative detection pose into the global map frame."""
        try:
            transform = self._tf_buffer.lookup_transform(
                'map',
                f'{self.robot_id}/base_link',
                Time(),
            )
        except Exception as exc:
            self.get_logger().warning(
                f'Waiting for map TF before confirming incident position: {exc}'
            )
            return None

        translation = transform.transform.translation
        rotation = transform.transform.rotation
        yaw = math.atan2(
            2.0 * (rotation.w * rotation.z + rotation.x * rotation.y),
            1.0 - 2.0 * (rotation.y * rotation.y + rotation.z * rotation.z),
        )
        transformed = Pose()
        transformed.position.x = (
            math.cos(yaw) * float(pose.position.x)
            - math.sin(yaw) * float(pose.position.y)
            + float(translation.x)
        )
        transformed.position.y = (
            math.sin(yaw) * float(pose.position.x)
            + math.cos(yaw) * float(pose.position.y)
            + float(translation.y)
        )
        transformed.position.z = float(pose.position.z) + float(translation.z)
        transformed.orientation = pose.orientation
        return transformed


def main(args=None):
    rclpy.init(args=args)
    node = FusionDecisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
