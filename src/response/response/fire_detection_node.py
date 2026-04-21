from importlib import import_module

import rclpy
from rclpy.node import Node

# Resolve the generated ROS message class dynamically to avoid static analyzer
# false positives when interface stubs are not discoverable in the IDE env.
FireDetection = getattr(import_module('firescout_interfaces.msg'), 'FireDetection')


class FireDetectionNode(Node):

    def __init__(self):

        # Node name
        super().__init__('fire_detection_node')

        # Declare parameters
        self.declare_parameter(
            'fire_confidence_threshold',
            0.7
        )

        self.declare_parameter(
            'robot_id',
            'robot1'
        )

        self.declare_parameter(
            'publish_demo_detections',
            False
        )

        # Get parameters
        self.threshold = self.get_parameter(
            'fire_confidence_threshold'
        ).value

        self.robot_id = self.get_parameter(
            'robot_id'
        ).value

        self.publish_demo_detections = self.get_parameter(
            'publish_demo_detections'
        ).value

        # Create publisher
        topic_name = f'/{self.robot_id}/fire_detection'

        self.publisher_ = self.create_publisher(
            FireDetection,
            topic_name,
            10
        )

        # Create timer
        self.timer = self.create_timer(
            2.0,
            self.timer_callback
        )

        self.get_logger().info(
            f"Fire Detection Node started for {self.robot_id}"
        )

    def timer_callback(self):

        if not self.publish_demo_detections:
            return

        # Fake confidence value
        fake_confidence = 0.8

        if fake_confidence >= self.threshold:

            msg = FireDetection()

            msg.robot_name = self.robot_id

            msg.confidence = fake_confidence
            msg.intensity = 0.6
            msg.temperature = 120.0

            msg.flame_coordinates = [1.0, 2.0]

            msg.detection_time = (
                self.get_clock()
                .now()
                .to_msg()
            )

            self.publisher_.publish(msg)

            self.get_logger().info(
                "Fire detected and published"
            )

        else:

            self.get_logger().info(
                "Fire confidence below threshold"
            )


def main(args=None):

    rclpy.init(args=args)

    node = FireDetectionNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
