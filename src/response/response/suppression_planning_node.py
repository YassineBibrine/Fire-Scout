from importlib import import_module

import rclpy
from rclpy.node import Node

# Resolve the generated ROS message classes dynamically to avoid static analyzer
# false positives when interface stubs are not discoverable in the IDE env.
FireDetection = getattr(import_module('firescout_interfaces.msg'), 'FireDetection')
Incident = getattr(import_module('firescout_interfaces.msg'), 'Incident')


class SuppressionPlanningNode(Node):

    def __init__(self):

        super().__init__('suppression_planning_node')

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

        topic_name = f'/{self.robot_id}/fire_detection'

        self.subscription = self.create_subscription(
            FireDetection,
            topic_name,
            self.fire_detection_callback,
            10
        )

        self.publisher_ = self.create_publisher(
            Incident,
            '/incidents/fire',
            10
        )

        self.get_logger().info(
            f"Suppression Planning Node started for {self.robot_id}"
        )

    def fire_detection_callback(self, detection):

        if detection.confidence <= 0.7:
            return

        self.seq += 1
        incident_id = f"fire_{self.robot_id}_{self.seq}"

        incident = Incident()
        incident.incident_id = incident_id
        incident.incident_type = 'FIRE'
        incident.robot_id = self.robot_id
        incident.position = detection.position
        incident.priority = detection.confidence
        incident.detection_time = (
            self.get_clock()
            .now()
            .to_msg()
        )
        incident.last_updated = incident.detection_time

        self.publisher_.publish(incident)

        self.get_logger().info(
            f"Suppression plan published for {incident_id}"
        )


def main(args=None):

    rclpy.init(args=args)

    node = SuppressionPlanningNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
