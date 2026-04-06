from monitoring.topic_rate_monitor_node import TopicRateMonitor


def test_topic_rate_alarm_triggers_when_rate_drops():
    monitor = TopicRateMonitor(minimum_rate_hz=2.0, window_s=2.0)
    monitor.record(0.0)
    monitor.record(2.0)
    assert monitor.alarm()


def test_topic_rate_alarm_clear_when_rate_ok():
    monitor = TopicRateMonitor(minimum_rate_hz=2.0, window_s=2.0)
    monitor.record(0.0)
    monitor.record(0.5)
    monitor.record(1.0)
    monitor.record(1.5)
    assert not monitor.alarm()

