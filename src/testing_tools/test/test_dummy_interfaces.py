from testing_tools import dummy_heartbeat_pub, dummy_odom_pub, dummy_scan_pub


def test_dummy_interfaces_have_main():
    assert callable(dummy_heartbeat_pub.main)
    assert callable(dummy_scan_pub.main)
    assert callable(dummy_odom_pub.main)
