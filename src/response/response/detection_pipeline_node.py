"""ROS 2 detection pipeline node for incident conversion."""

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from response.detection_processor import detection_to_incident


class DetectionPipelineNode(Node):
    def __init__(self):
        super().__init__('detection_pipeline_node')
        self.create_subscription(String, 'response/detections', self._on_detection, 10)
        self.pub = self.create_publisher(String, 'response/incidents', 10)

    def _on_detection(self, msg):
        try:
            payload = json.loads(msg.data)
            incident = detection_to_incident(
                payload['detection_type'],
                payload['robot_id'],
                float(payload.get('confidence', 0.0)),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            self.get_logger().warning('Invalid detection payload')
            return

        out = String()
        out.data = json.dumps(incident)
        self.pub.publish(out)


def main():
    rclpy.init()
    node = DetectionPipelineNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
