from importlib import import_module

import rclpy
from rclpy.node import Node

# Resolve the generated ROS message class dynamically to avoid static analyzer
# false positives when interface stubs are not discoverable in the IDE env.
HumanDetection = getattr(import_module('firescout_interfaces.msg'), 'HumanDetection')


class HumanDetectionNode(Node):

    def __init__(self):

        # Node name
        super().__init__('human_detection_node')

        # Declare parameters
        self.declare_parameter(
            'robot_id',
            'robot1'
        )

        self.declare_parameter(
            'human_confidence_threshold',
            0.6
        )

        self.declare_parameter(
            'publish_demo_detections',
            False
        )

        self.declare_parameter(
            'use_sim_time',
            True
        )

        # Get parameters
        self.robot_id = self.get_parameter(
            'robot_id'
        ).value

        self.threshold = self.get_parameter(
            'human_confidence_threshold'
        ).value

        self.publish_demo_detections = self.get_parameter(
            'publish_demo_detections'
        ).value

        # Create publisher
        topic_name = f'/{self.robot_id}/human_detection'

        self.publisher_ = self.create_publisher(
            HumanDetection,
            topic_name,
            10
        )

        # Create timer
        self.timer = self.create_timer(
            2.0,
            self.timer_callback
        )

        self.get_logger().info(
            f"Human Detection Node started for {self.robot_id}"
        )

    def timer_callback(self):

        if not self.publish_demo_detections:
            return

        fake_confidence = 0.75

        if fake_confidence >= self.threshold:

            msg = HumanDetection()

            msg.robot_name = self.robot_id
            msg.confidence = fake_confidence
            msg.is_moving = True
            msg.needs_rescue = False
            msg.bounding_box = [0.0, 0.0, 1.0, 1.0]

            msg.detection_time = (
                self.get_clock()
                .now()
                .to_msg()
            )

            self.publisher_.publish(msg)

        else:

            self.get_logger().info(
                "Human confidence below threshold"
            )


def main(args=None):

    rclpy.init(args=args)

    node = HumanDetectionNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
