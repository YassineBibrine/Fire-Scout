"""Latency monitor primitives for v1 thresholds."""


class LatencyMonitor:
    def __init__(self, threshold_s):
        self.threshold_s = threshold_s
        self.last_latency_s = 0.0

    def observe(self, sent_ts_s, recv_ts_s):
        self.last_latency_s = max(0.0, recv_ts_s - sent_ts_s)
        return self.last_latency_s > self.threshold_s


def main():
    print('latency_monitor_node v1 ready')


if __name__ == '__main__':
    main()
