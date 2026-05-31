from importlib import import_module

import rclpy
from rclpy.node import Node
from rclpy.time import Time

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

        self._latest_sensor: FireSensorAlert | None = None
        self._latest_vision: VisionDetectionArray | None = None
        self._last_confirmed: Time | None = None

        self._sensor_sub = self.create_subscription(
            FireSensorAlert,
            f'/{self.robot_id}/fire_sensor_alert',
            self._sensor_cb,
            10,
        )
        self._vision_sub = self.create_subscription(
            VisionDetectionArray,
            f'/{self.robot_id}/camera_detections',
            self._vision_cb,
            10,
        )
        self._pub = self.create_publisher(
            FusionDecision,
            f'/{self.robot_id}/fusion_decision',
            10,
        )

        self.get_logger().info(
            f'FusionDecisionNode started for {self.robot_id} '
            f'window={self._window_sec}s sensor_thr={self._sensor_thr} '
            f'vision_thr={self._vision_thr}'
        )

    # ------------------------------------------------------------------
    # Subscription callbacks
    # ------------------------------------------------------------------

    def _sensor_cb(self, msg: FireSensorAlert) -> None:
        self._latest_sensor = msg
        self._try_fuse()

    def _vision_cb(self, msg: VisionDetectionArray) -> None:
        self._latest_vision = msg
        self._try_fuse()

    # ------------------------------------------------------------------
    # Fusion logic
    # ------------------------------------------------------------------

    def _try_fuse(self) -> None:
        if self._latest_sensor is None or self._latest_vision is None:
            return

        now = self.get_clock().now()

        # --- Staleness check -----------------------------------------
        sensor_time = Time.from_msg(self._latest_sensor.timestamp)
        vision_time = Time.from_msg(self._latest_vision.timestamp)

        sensor_age = (now - sensor_time).nanoseconds / _NS_PER_SEC
        vision_age = (now - vision_time).nanoseconds / _NS_PER_SEC
        temporal_gap = abs(
            (sensor_time - vision_time).nanoseconds
        ) / _NS_PER_SEC

        if sensor_age > self._window_sec:
            self.get_logger().debug('Sensor data stale; skipping fusion.')
            return
        if vision_age > self._window_sec:
            self.get_logger().debug('Vision data stale; skipping fusion.')
            return
        if temporal_gap > self._window_sec:
            self.get_logger().debug(
                f'Sensor/vision gap {temporal_gap:.1f}s > window; skipping.'
            )
            return

        # --- Sensor evaluation ---------------------------------------
        sensor_fire = (
            self._latest_sensor.flame_detected
            or self._latest_sensor.normalized_risk >= self._sensor_thr
        )
        sensor_conf = self._latest_sensor.normalized_risk

        # --- Vision evaluation ---------------------------------------
        fire_dets = [
            d for d in self._latest_vision.detections
            if d.class_label in ('fire', 'smoke')
            and d.confidence >= self._vision_thr
        ]
        human_dets = [
            d for d in self._latest_vision.detections
            if d.class_label == 'human'
            and d.confidence >= self._vision_thr
        ]
        vision_fire = len(fire_dets) > 0
        vision_conf = max(
            (d.confidence for d in fire_dets), default=0.0
        )

        # --- 2-of-2 fire confirmation --------------------------------
        fire_confirmed = sensor_fire and vision_fire

        # --- Human confirmed by vision alone -------------------------
        human_confirmed = len(human_dets) > 0

        if not fire_confirmed and not human_confirmed:
            return

        # --- Duplicate suppression -----------------------------------
        if self._last_confirmed is not None:
            elapsed = (now - self._last_confirmed).nanoseconds / _NS_PER_SEC
            if elapsed < self._cooldown_sec:
                self.get_logger().debug('Duplicate confirmation suppressed.')
                return

        self._last_confirmed = now

        # --- Build decision ------------------------------------------
        if fire_confirmed:
            risk = (sensor_conf + vision_conf) / 2.0
            action = 'SUPPRESS'
            out_vision_conf = vision_conf
        elif human_confirmed:
            best_human_conf = max(d.confidence for d in human_dets)
            risk = best_human_conf * 0.7
            action = 'RESCUE'
            # vision_confidence carries human confidence so human_detection_node
            # can apply its threshold correctly (vision_conf is fire-only = 0.0 here)
            out_vision_conf = best_human_conf
        else:
            risk = 0.0
            action = 'MONITOR'
            out_vision_conf = vision_conf

        sources = []
        if sensor_fire:
            sources.append(f'sensor:{self._latest_sensor.source_id}')
        if vision_fire or human_confirmed:
            sources.append(f'camera:{self._latest_vision.camera_id}')

        decision = FusionDecision()
        decision.robot_id = self.robot_id
        decision.fire_confirmed = fire_confirmed
        decision.human_confirmed = human_confirmed
        decision.risk_level = float(risk)
        decision.recommended_action = action
        decision.contributing_sources = sources
        decision.sensor_confidence = float(sensor_conf)
        decision.vision_confidence = float(out_vision_conf)
        decision.timestamp = now.to_msg()

        self._pub.publish(decision)
        self.get_logger().info(
            f'FusionDecision: fire={fire_confirmed} human={human_confirmed} '
            f'risk={risk:.2f} action={action}'
        )


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

