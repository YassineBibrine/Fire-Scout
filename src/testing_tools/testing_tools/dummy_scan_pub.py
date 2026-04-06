"""Dummy scan payload generator for tests."""


def generate_scan(robot_id, ranges):
    return {
        'topic': f'/{robot_id}/scan',
        'ranges': list(ranges),
    }


def main():
    print('dummy_scan_pub v1 ready')


if __name__ == '__main__':
    main()
