from exploration.auction_orchestrator import resolve_with_timeout


def test_bid_timeout_returns_none_before_deadline():
    winner = resolve_with_timeout({'robot1': 1.0}, opened_at_s=10.0, now_s=10.9, timeout_s=1.0)
    assert winner is None


def test_bid_timeout_returns_winner_after_deadline():
    winner = resolve_with_timeout({'robot1': 1.0, 'robot2': 2.0}, opened_at_s=10.0, now_s=11.0, timeout_s=1.0)
    assert winner == 'robot2'

