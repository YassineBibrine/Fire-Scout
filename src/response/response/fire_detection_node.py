from importlib import import_module

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Pose

FusionDecision = getattr(import_module('firescout_interfaces.msg'), 'FusionDecision')
FireDetection = getattr(import_module('firescout_interfaces.msg'), 'FireDetection')


class FireDetectionNode(Node):
    """
    Phase 2 hybrid fire detection.

    Converts a FusionDecision (fire_confirmed=True) into a FireDetection
    message that the downstream suppression planner consumes.  Fire
    incidents are ONLY generated after 2-of-2 sensor+camera confirmation
    by the fusion pipeline.

    Subscribes : /{robot_id}/fusion_decision  (FusionDecision)
    Publishes  : /{robot_id}/fire_detection   (FireDetection)

    Demo mode (publish_demo_detections=True) bypasses fusion and emits
    synthetic detections on a 2-second timer for integration testing.
    """

    def __init__(self):
        super().__init__('fire_detection_node')

        self.declare_parameter('fire_confidence_threshold', 0.7)
        self.declare_parameter('robot_id', 'robot1')
        self.declare_parameter('publish_demo_detections', False)
        if not self.has_parameter('use_sim_time'):
            self.declare_parameter('use_sim_time', False)

        self.threshold: float = self.get_parameter(
            'fire_confidence_threshold'
        ).value
        self.robot_id: str = self.get_parameter('robot_id').value
        self.publish_demo_detections: bool = self.get_parameter(
            'publish_demo_detections'
        ).value

        self.publisher_ = self.create_publisher(
            FireDetection,
            f'/{self.robot_id}/fire_detection',
            10,
        )

        if self.publish_demo_detections:
            # Demo timer: emits synthetic detections without fusion.
            self.timer = self.create_timer(2.0, self._demo_callback)
            self.get_logger().warn(
                f'FireDetectionNode [{self.robot_id}]: '
                'demo mode active (publish_demo_detections=true)'
            )
        else:
            # Production: subscribe to the fusion pipeline.
            self._fusion_sub = self.create_subscription(
                FusionDecision,
                f'/{self.robot_id}/fusion_decision',
                self._fusion_callback,
                10,
            )

        self.get_logger().info(
            f'FireDetectionNode started for {self.robot_id} '
            f'[{"demo" if self.publish_demo_detections else "hybrid"}]'
        )

    # ------------------------------------------------------------------
    # Fusion-driven path (production)
    # ------------------------------------------------------------------

    def _fusion_callback(self, msg: FusionDecision) -> None:
        if not msg.fire_confirmed:
            return

        combined_confidence = (msg.sensor_confidence + msg.vision_confidence) / 2.0

        if combined_confidence < self.threshold:
            self.get_logger().debug(
                f'Fusion confirmed fire but combined confidence '
                f'{combined_confidence:.2f} < threshold {self.threshold}'
            )
            return

        detection = FireDetection()
        detection.robot_name = self.robot_id
        detection.confidence = combined_confidence
        detection.intensity = msg.risk_level
        detection.temperature = 0.0   # raw temperature not forwarded through fusion
        detection.flame_coordinates = []
        detection.position = Pose()   # pose not propagated through FusionDecision
        detection.detection_time = msg.timestamp

        self.publisher_.publish(detection)
        self.get_logger().info(
            f'FireDetection published: robot={self.robot_id} '
            f'confidence={combined_confidence:.2f} risk={msg.risk_level:.2f}'
        )

    # ------------------------------------------------------------------
    # Demo path (testing / CI)
    # ------------------------------------------------------------------

    def _demo_callback(self) -> None:
        fake_confidence = 0.8
        if fake_confidence < self.threshold:
            self.get_logger().info('Fire confidence below threshold')
            return

        msg = FireDetection()
        msg.robot_name = self.robot_id
        msg.confidence = fake_confidence
        msg.intensity = 0.6
        msg.temperature = 120.0
        msg.position = self._build_demo_pose()
        msg.flame_coordinates = [1.0, 2.0]
        msg.detection_time = self.get_clock().now().to_msg()

        self.publisher_.publish(msg)
        self.get_logger().info('Fire detected and published')

    def _build_demo_pose(self) -> Pose:
        pose = Pose()
        pose.position.x = 1.0
        pose.position.y = 2.0
        pose.position.z = 0.0
        pose.orientation.w = 1.0
        return pose


def main(args=None):
    rclpy.init(args=args)
    node = FireDetectionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()

