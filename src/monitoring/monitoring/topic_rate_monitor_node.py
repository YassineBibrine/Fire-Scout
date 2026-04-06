"""Topic rate monitor primitives for v1 thresholds."""


class TopicRateMonitor:
    def __init__(self, minimum_rate_hz, window_s=1.0):
        self.minimum_rate_hz = minimum_rate_hz
        self.window_s = window_s
        self.timestamps = []

    def record(self, timestamp_s):
        self.timestamps.append(timestamp_s)
        cutoff = timestamp_s - self.window_s
        self.timestamps = [ts for ts in self.timestamps if ts >= cutoff]

    def current_rate(self):
        if len(self.timestamps) < 2:
            return 0.0
        span = self.timestamps[-1] - self.timestamps[0]
        if span <= 0.0:
            return 0.0
        return (len(self.timestamps) - 1) / span

    def alarm(self):
        return self.current_rate() < self.minimum_rate_hz


def main():
    print('topic_rate_monitor_node v1 ready')


if __name__ == '__main__':
    main()
