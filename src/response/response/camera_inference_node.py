from importlib import import_module
from typing import Any

import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
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
        model_path            – path to inference model; required outside debug stub mode
        confidence_threshold  – minimum per-detection confidence (default: 0.5)
    """

    def __init__(self):
        super().__init__('camera_inference_node')

        self.declare_parameter('robot_id', 'robot1')
        self.declare_parameter('model_path', '')
        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('allow_stub_inference', False)
        if not self.has_parameter('use_sim_time'):
            self.declare_parameter('use_sim_time', False)

        self.robot_id = self.get_parameter('robot_id').value
        self.model_path: str = self.get_parameter('model_path').value
        self.confidence_threshold: float = (
            self.get_parameter('confidence_threshold').value
        )
        self.allow_stub_inference = bool(
            self.get_parameter('allow_stub_inference').value
        )

        self._model = self._load_model()

        camera_detections_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.BEST_EFFORT,
        )
        self._sub = self.create_subscription(
            Image,
            f'/{self.robot_id}/camera/image_raw',
            self._image_callback,
            qos_profile_sensor_data,
        )

        self._pub = self.create_publisher(
            VisionDetectionArray,
            f'/{self.robot_id}/camera_detections',
            camera_detections_qos,
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
            if self.allow_stub_inference:
                self.get_logger().warn(
                    'model_path not set; debug stub inference is enabled.'
                )
                return None
            raise RuntimeError(
                'model_path is required unless allow_stub_inference=true'
            )
        try:
            yolo_class = getattr(import_module('ultralytics'), 'YOLO')
            model = yolo_class(self.model_path)
            self.get_logger().info(f'Loaded model from {self.model_path}')
            return model
        except Exception as exc:
            if self.allow_stub_inference:
                self.get_logger().error(
                    f'Failed to load model from "{self.model_path}": {exc}. '
                    'Debug stub inference remains enabled.'
                )
                return None
            raise RuntimeError(
                f'Failed to load inference model "{self.model_path}": {exc}'
            ) from exc

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
        """Run Ultralytics YOLO inference and return Fire-Scout detections."""
        np = import_module('numpy')

        channels = 3
        expected_size = int(msg.width) * int(msg.height) * channels
        if msg.encoding.lower() not in ('rgb8', 'bgr8') or len(msg.data) < expected_size:
            self.get_logger().warning(
                f'Unsupported image encoding/size: {msg.encoding} bytes={len(msg.data)}'
            )
            return []

        frame = np.frombuffer(msg.data, dtype=np.uint8, count=expected_size)
        frame = frame.reshape((int(msg.height), int(msg.width), channels))
        if msg.encoding.lower() == 'rgb8':
            frame = frame[:, :, ::-1]

        detections = []
        model: Any = self._model
        for result in model.predict(
            source=frame,
            conf=self.confidence_threshold,
            verbose=False,
        ):
            names = result.names
            for box in result.boxes:
                class_index = int(box.cls[0])
                label = str(names[class_index]).lower()
                if label not in ('fire', 'smoke', 'human', 'person'):
                    continue
                detection = Detection()
                detection.class_label = 'human' if label == 'person' else label
                detection.confidence = float(box.conf[0])
                detection.bounding_box = [
                    float(value) for value in box.xyxy[0].tolist()
                ]
                detection.estimated_pose.orientation.w = 1.0
                detections.append(detection)
        return detections


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
