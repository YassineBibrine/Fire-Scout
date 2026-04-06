"""Dummy heartbeat payload generator for tests."""


def generate_heartbeat(robot_id, timestamp_s):
    return {
        'topic': f'/{robot_id}/heartbeat',
        'robot_id': robot_id,
        'timestamp_s': timestamp_s,
    }


def main():
    print('dummy_heartbeat_pub v1 ready')


if __name__ == '__main__':
    main()
