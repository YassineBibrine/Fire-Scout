"""Dummy fault injection payload generator for tests."""


def inject_fault(robot_id, fault_type, severity='warning'):
    return {
        'robot_id': robot_id,
        'fault_type': fault_type,
        'severity': severity,
    }


def main():
    print('dummy_fault_injector v1 ready')


if __name__ == '__main__':
    main()
