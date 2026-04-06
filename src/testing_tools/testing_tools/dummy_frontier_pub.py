"""Dummy frontier payload generator for tests."""


def generate_frontier(robot_id, points):
    return {
        'topic': f'/{robot_id}/frontiers',
        'points': list(points),
    }


def main():
    print('dummy_frontier_pub v1 ready')


if __name__ == '__main__':
    main()
