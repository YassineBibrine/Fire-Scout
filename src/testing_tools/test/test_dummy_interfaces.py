from testing_tools.dummy_camera_pub import generate_camera_frame
from testing_tools.dummy_heartbeat_pub import generate_heartbeat
from testing_tools.dummy_odom_pub import generate_odom
from testing_tools.dummy_scan_pub import generate_scan


def test_dummy_interfaces_publish_namespaced_payloads():
    scan = generate_scan('robot1', [1.0, 2.0])
    odom = generate_odom('robot1', 1.2, -0.3, 0.1)
    camera = generate_camera_frame('robot1', width=640, height=480)
    heartbeat = generate_heartbeat('robot1', timestamp_s=42.0)

    assert scan['topic'] == '/robot1/scan'
    assert odom['topic'] == '/robot1/odom'
    assert camera['topic'] == '/robot1/camera/image_raw'
    assert heartbeat['topic'] == '/robot1/heartbeat'
