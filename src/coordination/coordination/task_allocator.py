"""Simple task allocation utilities for v1 auction flow."""


def choose_winner(bids):
    """Pick the best bid by lowest cost, tie-breaking by robot id."""
    if not bids:
        return None

    return min(bids.items(), key=lambda item: (item[1], item[0]))[0]


def assign_task(task_id, bids):
    """Return a v1 assignment record for a task and bid map."""
    winner = choose_winner(bids)
    return {
        'task_id': task_id,
        'winner': winner,
        'bid_count': len(bids),
    }
