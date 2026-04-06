"""Heartbeat monitoring helpers for robot health checks."""


def heartbeat_timed_out(last_seen_s, now_s, timeout_s=2.0):
    """Return True when the elapsed time exceeds the heartbeat timeout."""
    if now_s < last_seen_s:
        return False
    return (now_s - last_seen_s) > timeout_s
