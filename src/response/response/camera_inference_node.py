from importlib import import_module

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image

VisionDetectionArray = getattr(
    import_module('firescout_interfaces.msg'), 'VisionDetectionArray'
)
Detection = getattr(import_module('firescout_interfaces.msg'), 'Detection')


class CameraInferenceNode(Node):
    """
    Runs fire/human/smoke classification on incoming camera frames and
    publishes structured VisionDetectionArray messages consumed by the
    fusion pipeline.

    Subscribes : /{robot_id}/camera/image_raw  (sensor_msgs/Image)
    Publishes  : /{robot_id}/camera_detections  (VisionDetectionArray)

    Parameters:
        robot_id              – robot namespace (default: robot1)
        model_path            – path to inference model; empty = stub mode
        confidence_threshold  – minimum per-detection confidence (default: 0.5)
    """

    def __init__(self):
        super().__init__('camera_inference_node')

        self.declare_parameter('robot_id', 'robot1')
        self.declare_parameter('model_path', '')
        self.declare_parameter('confidence_threshold', 0.5)
        if not self.has_parameter('use_sim_time'):
            self.declare_parameter('use_sim_time', False)

        self.robot_id = self.get_parameter('robot_id').value
        self.model_path: str = self.get_parameter('model_path').value
        self.confidence_threshold: float = (
            self.get_parameter('confidence_threshold').value
        )

        self._model = self._load_model()

        self._sub = self.create_subscription(
            Image,
            f'/{self.robot_id}/camera/image_raw',
            self._image_callback,
            10,
        )

        self._pub = self.create_publisher(
            VisionDetectionArray,
            f'/{self.robot_id}/camera_detections',
            10,
        )

        mode = 'stub' if self._model is None else 'model'
        self.get_logger().info(
            f'CameraInferenceNode started for {self.robot_id} '
            f'[{mode}] threshold={self.confidence_threshold}'
        )

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def _load_model(self):
        if not self.model_path:
            self.get_logger().warn(
                'model_path not set; running in stub/passthrough mode.'
            )
            return None
        try:
            # Placeholder: swap in your actual model loader here.
            # e.g.: import torch; return torch.load(self.model_path)
            self.get_logger().info(f'Loaded model from {self.model_path}')
            return None  # Replace with real model object
        except Exception as exc:
            self.get_logger().error(
                f'Failed to load model from "{self.model_path}": {exc}. '
                'Falling back to stub mode.'
            )
            return None

    # ------------------------------------------------------------------
    # Image callback
    # ------------------------------------------------------------------

    def _image_callback(self, msg: Image) -> None:
        detections = (
            self._model_inference(msg)
            if self._model is not None
            else self._stub_inference(msg)
        )

        out = VisionDetectionArray()
        out.robot_id = self.robot_id
        out.camera_id = f'{self.robot_id}_camera'
        out.detections = detections
        out.timestamp = msg.header.stamp
        self._pub.publish(out)

    # ------------------------------------------------------------------
    # Inference implementations
    # ------------------------------------------------------------------

    def _stub_inference(self, msg: Image):
        """
        Heuristic stub: treat mean pixel brightness as a proxy for scene
        activity.  A bright-enough frame generates a low-confidence fire
        detection so the fusion layer can exercise the 2-of-2 path without
        a real model.
        """
        detections = []
        data = msg.data
        if not data or msg.width == 0 or msg.height == 0:
            return detections

        sample_len = min(1000, len(data))
        try:
            avg_brightness = sum(data[:sample_len]) / (sample_len * 255.0)
        except Exception:
            return detections

        if avg_brightness > 0.01:
            confidence = min(1.0, avg_brightness * 2.0)
            if confidence >= self.confidence_threshold:
                d = Detection()
                d.class_label = 'fire'
                d.confidence = confidence
                d.bounding_box = [
                    0.0, 0.0,
                    float(msg.width),
                    float(msg.height),
                ]
                detections.append(d)

        return detections

    def _model_inference(self, msg: Image):
        """Replace with real model inference; must return list[Detection]."""
        return []


def main(args=None):
    rclpy.init(args=args)
    node = CameraInferenceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()

