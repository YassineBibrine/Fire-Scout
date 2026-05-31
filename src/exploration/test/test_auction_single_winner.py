from exploration.auction_logic import AuctionBid, select_winner


def test_auction_single_winner_is_deterministic():
    bids = [
        AuctionBid('a1', 'robot2', 'f1', utility_score=3.0, eta_sec=3.0, energy_cost=1.0),
        AuctionBid('a1', 'robot1', 'f1', utility_score=3.0, eta_sec=2.0, energy_cost=1.2),
        AuctionBid('a1', 'robot3', 'f1', utility_score=2.5, eta_sec=1.0, energy_cost=0.5),
    ]

    winner = select_winner(bids, timeout_sec=5.0)

    assert winner is not None
    assert winner.winner.robot_id == 'robot1'
    assert winner.considered_count == 3
