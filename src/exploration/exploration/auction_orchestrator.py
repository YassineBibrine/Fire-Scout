"""Auction selection primitives for exploration tasks."""


def select_single_winner(bids):
    """Select winner by highest score, tie-breaking by robot id."""
    if not bids:
        return None
    ranked = sorted(bids.items(), key=lambda item: (-item[1], item[0]))
    return ranked[0][0]


def resolve_with_timeout(bids, opened_at_s, now_s, timeout_s):
    """Resolve an auction only once timeout has elapsed."""
    if (now_s - opened_at_s) < timeout_s:
        return None
    return select_single_winner(bids)
