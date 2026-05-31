import rclpy
from rclpy.node import Node


class NamespaceLintNode(Node):

    def __init__(self):

        super().__init__('namespace_lint_node')

        self.allowed_prefixes = (
            '/robot1',
            '/robot2',
            '/robot3',
            '/mapping',
            '/coordination',
            '/incidents',
            '/mission',
            '/monitoring',
            '/model'
        )

        self.timer = self.create_timer(
            5.0,
            self.check_namespaces
        )
        self.has_checked = False

    def check_namespaces(self):

        if self.has_checked:
            return

        self.has_checked = True

        topics = self.get_topic_names_and_types()
        for topic_name, _types in topics:
            if not topic_name.startswith(self.allowed_prefixes):
                self.get_logger().warning(
                    f'Topic violates namespace policy: {topic_name}'
                )

        self.destroy_node()
        rclpy.shutdown()


def main(args=None):

    rclpy.init(args=args)

    node = NamespaceLintNode()

    rclpy.spin(node)


if __name__ == '__main__':
    main()
