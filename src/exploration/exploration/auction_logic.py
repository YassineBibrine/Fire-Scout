from dataclasses import dataclass
from typing import Iterable, List, Optional, Set


@dataclass(frozen=True)
class AuctionBid:
    auction_id: str
    robot_id: str
    candidate_frontier_id: str
    utility_score: float
    eta_sec: float
    energy_cost: float


@dataclass(frozen=True)
class AuctionSelection:
    winner: AuctionBid
    considered_count: int


def select_winner(
    bids: Iterable[AuctionBid],
    timeout_sec: float,
    eligible_robot_ids: Optional[Set[str]] = None,
) -> Optional[AuctionSelection]:
    """Select the winning bid with deterministic tie breaking.

    Only bids with eta <= timeout and (if provided) robot in eligible set are considered.
    """
    candidates: List[AuctionBid] = []
    for bid in bids:
        if bid.eta_sec > timeout_sec:
            continue
        if eligible_robot_ids is not None and bid.robot_id not in eligible_robot_ids:
            continue
        candidates.append(bid)

    if not candidates:
        return None

    winner = min(
        candidates,
        key=lambda bid: (-bid.utility_score, bid.eta_sec, bid.energy_cost, bid.robot_id),
    )
    return AuctionSelection(winner=winner, considered_count=len(candidates))
