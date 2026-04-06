from monitoring.latency_monitor_node import LatencyMonitor


def test_latency_alarm_triggers_when_threshold_exceeded():
    monitor = LatencyMonitor(threshold_s=0.2)
    assert monitor.observe(sent_ts_s=10.0, recv_ts_s=10.3)


def test_latency_alarm_clear_when_below_threshold():
    monitor = LatencyMonitor(threshold_s=0.2)
    assert not monitor.observe(sent_ts_s=10.0, recv_ts_s=10.1)

