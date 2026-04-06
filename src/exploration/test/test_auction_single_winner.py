from exploration.auction_orchestrator import select_single_winner


def test_auction_single_winner():
    winner = select_single_winner({'robot1': 0.7, 'robot2': 0.9, 'robot3': 0.8})
    assert winner == 'robot2'

