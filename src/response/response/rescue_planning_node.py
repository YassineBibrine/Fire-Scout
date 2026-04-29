from importlib import import_module

import rclpy
from rclpy.node import Node

# Resolve the generated ROS message classes dynamically to avoid static analyzer
# false positives when interface stubs are not discoverable in the IDE env.
HumanDetection = getattr(import_module('firescout_interfaces.msg'), 'HumanDetection')
Incident = getattr(import_module('firescout_interfaces.msg'), 'Incident')


class RescuePlanningNode(Node):

    def __init__(self):

        super().__init__('rescue_planning_node')

        self.declare_parameter(
            'robot_id',
            'robot1'
        )

        self.declare_parameter(
            'use_sim_time',
            True
        )

        self.robot_id = self.get_parameter(
            'robot_id'
        ).value

        self.seq = 0

        topic_name = f'/{self.robot_id}/human_detection'

        self.subscription = self.create_subscription(
            HumanDetection,
            topic_name,
            self.human_detection_callback,
            10
        )

        self.publisher_ = self.create_publisher(
            Incident,
            '/incidents/human',
            10
        )

        self.get_logger().info(
            f"Rescue Planning Node started for {self.robot_id}"
        )

    def human_detection_callback(self, detection):

        if not detection.needs_rescue and detection.confidence <= 0.6:
            return

        self.seq += 1
        incident_id = f"rescue_{self.robot_id}_{self.seq}"

        incident = Incident()
        incident.incident_id = incident_id
        incident.incident_type = 'HUMAN'
        incident.robot_id = self.robot_id
        incident.position = detection.position
        incident.priority = min(detection.confidence * 1.5, 1.0)
        incident.detection_time = (
            self.get_clock()
            .now()
            .to_msg()
        )
        incident.last_updated = incident.detection_time

        self.publisher_.publish(incident)

        self.get_logger().info(
            f"Rescue plan published for {incident_id}"
        )


def main(args=None):

    rclpy.init(args=args)

    node = RescuePlanningNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
