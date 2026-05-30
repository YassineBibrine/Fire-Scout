from importlib import import_module

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Pose

FusionDecision = getattr(import_module('firescout_interfaces.msg'), 'FusionDecision')
HumanDetection = getattr(import_module('firescout_interfaces.msg'), 'HumanDetection')


class HumanDetectionNode(Node):
    """
    Phase 2 hybrid human detection.

    Converts a FusionDecision (human_confirmed=True) into a HumanDetection
    message consumed by the rescue planner.  In the hybrid pipeline, human
    confirmation is vision-only (no physical-sensor equivalent).

    Subscribes : /{robot_id}/fusion_decision  (FusionDecision)
    Publishes  : /{robot_id}/human_detection  (HumanDetection)

    Demo mode (publish_demo_detections=True) bypasses fusion and emits
    synthetic detections on a 2-second timer for integration testing.
    """

    def __init__(self):
        super().__init__('human_detection_node')

        self.declare_parameter('robot_id', 'robot1')
        self.declare_parameter('human_confidence_threshold', 0.6)
        self.declare_parameter('publish_demo_detections', False)
        if not self.has_parameter('use_sim_time'):
            self.declare_parameter('use_sim_time', False)

        self.robot_id: str = self.get_parameter('robot_id').value
        self.threshold: float = self.get_parameter(
            'human_confidence_threshold'
        ).value
        self.publish_demo_detections: bool = self.get_parameter(
            'publish_demo_detections'
        ).value

        self.publisher_ = self.create_publisher(
            HumanDetection,
            f'/{self.robot_id}/human_detection',
            10,
        )

        if self.publish_demo_detections:
            self.timer = self.create_timer(2.0, self._demo_callback)
            self.get_logger().warn(
                f'HumanDetectionNode [{self.robot_id}]: '
                'demo mode active (publish_demo_detections=true)'
            )
        else:
            self._fusion_sub = self.create_subscription(
                FusionDecision,
                f'/{self.robot_id}/fusion_decision',
                self._fusion_callback,
                10,
            )

        self.get_logger().info(
            f'HumanDetectionNode started for {self.robot_id} '
            f'[{"demo" if self.publish_demo_detections else "hybrid"}]'
        )

    # ------------------------------------------------------------------
    # Fusion-driven path (production)
    # ------------------------------------------------------------------

    def _fusion_callback(self, msg: FusionDecision) -> None:
        if not msg.human_confirmed:
            return

        # vision_confidence carries the human detection confidence from camera_inference
        confidence = msg.vision_confidence
        if confidence < self.threshold:
            self.get_logger().debug(
                f'Human confirmed by fusion but confidence '
                f'{confidence:.2f} < threshold {self.threshold}'
            )
            return

        detection = HumanDetection()
        detection.robot_name = self.robot_id
        detection.confidence = confidence
        detection.is_moving = False   # not determinable from FusionDecision alone
        detection.needs_rescue = True  # conservative: always flag for rescue
        detection.bounding_box = []
        detection.position = Pose()
        detection.detection_time = msg.timestamp

        self.publisher_.publish(detection)
        self.get_logger().info(
            f'HumanDetection published: robot={self.robot_id} '
            f'confidence={confidence:.2f}'
        )

    # ------------------------------------------------------------------
    # Demo path (testing / CI)
    # ------------------------------------------------------------------

    def _demo_callback(self) -> None:
        fake_confidence = 0.75

        if fake_confidence < self.threshold:
            self.get_logger().info('Human confidence below threshold')
            return

        msg = HumanDetection()
        msg.robot_name = self.robot_id
        msg.confidence = fake_confidence
        msg.is_moving = True
        msg.needs_rescue = False
        msg.position = self._build_demo_pose()
        msg.bounding_box = [0.0, 0.0, 1.0, 1.0]
        msg.detection_time = self.get_clock().now().to_msg()

        self.publisher_.publish(msg)

    def _build_demo_pose(self) -> Pose:
        pose = Pose()
        pose.position.x = 0.5
        pose.position.y = 1.0
        pose.position.z = 0.0
        pose.orientation.w = 1.0
        return pose


def main(args=None):
    rclpy.init(args=args)
    node = HumanDetectionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()

