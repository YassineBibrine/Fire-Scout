from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class FrontierCandidate:
    frontier_id: str
    robot_id: str
    area_m2: float
    info_gain: float
    travel_cost: float
    reachable: bool = True


def select_frontiers(
    frontiers: Iterable[FrontierCandidate],
    min_size: float,
    max_travel_cost: float,
) -> List[FrontierCandidate]:
    """Filter frontiers and return a deterministic rank order."""
    filtered = [
        frontier
        for frontier in frontiers
        if frontier.reachable
        and frontier.area_m2 >= min_size
        and frontier.travel_cost <= max_travel_cost
    ]
    return sorted(
        filtered,
        key=lambda frontier: (-frontier.info_gain, frontier.travel_cost, frontier.frontier_id),
    )
