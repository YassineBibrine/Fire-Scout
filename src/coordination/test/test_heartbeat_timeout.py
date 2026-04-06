from coordination.heartbeat_monitor import heartbeat_timed_out


def test_heartbeat_timeout_triggers_after_threshold():
    assert heartbeat_timed_out(last_seen_s=10.0, now_s=12.1, timeout_s=2.0)


def test_heartbeat_timeout_not_triggered_within_threshold():
    assert not heartbeat_timed_out(last_seen_s=10.0, now_s=11.9, timeout_s=2.0)

