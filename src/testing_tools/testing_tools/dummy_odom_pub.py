"""Dummy odom payload generator for tests."""


def generate_odom(robot_id, x, y, yaw):
    return {
        'topic': f'/{robot_id}/odom',
        'pose': {'x': x, 'y': y, 'yaw': yaw},
    }


def main():
    print('dummy_odom_pub v1 ready')


if __name__ == '__main__':
    main()
