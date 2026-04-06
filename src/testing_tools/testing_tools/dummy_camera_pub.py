"""Dummy camera payload generator for tests."""


def generate_camera_frame(robot_id, width, height, encoding='rgb8'):
    return {
        'topic': f'/{robot_id}/camera/image_raw',
        'width': width,
        'height': height,
        'encoding': encoding,
    }


def main():
    print('dummy_camera_pub v1 ready')


if __name__ == '__main__':
    main()
