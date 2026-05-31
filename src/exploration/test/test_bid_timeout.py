from exploration.auction_logic import AuctionBid, select_winner


def test_bid_timeout_filters_late_bids():
    bids = [
        AuctionBid('a2', 'robot1', 'f2', utility_score=4.0, eta_sec=8.0, energy_cost=2.0),
        AuctionBid('a2', 'robot2', 'f2', utility_score=3.5, eta_sec=1.5, energy_cost=1.1),
    ]

    winner = select_winner(bids, timeout_sec=2.0)

    assert winner is not None
    assert winner.winner.robot_id == 'robot2'
    assert winner.considered_count == 1


def test_bid_timeout_returns_none_when_all_late():
    bids = [
        AuctionBid('a3', 'robot1', 'f3', utility_score=5.0, eta_sec=4.0, energy_cost=0.9),
        AuctionBid('a3', 'robot2', 'f3', utility_score=4.0, eta_sec=6.0, energy_cost=1.1),
    ]

    assert select_winner(bids, timeout_sec=1.0) is None
