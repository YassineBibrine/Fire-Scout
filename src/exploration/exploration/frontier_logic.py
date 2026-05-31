from dataclasses import dataclass
from typing import Iterable, List

HAZARD_RISK_THRESHOLD = 0.7
HAZARD_TRAVEL_COST_MULTIPLIER = 3.0


@dataclass(frozen=True)
class FrontierCandidate:
    frontier_id: str
    robot_id: str
    area_m2: float
    info_gain: float
    travel_cost: float
    reachable: bool = True
    centroid_x: float = 0.0
    centroid_y: float = 0.0


def select_frontiers(
    frontiers: Iterable[FrontierCandidate],
    min_size: float,
    max_travel_cost: float,
    hazard_decision=None,
) -> List[FrontierCandidate]:
    """Filter frontiers and return a deterministic rank order."""
    scored_frontiers = apply_hazard_weighting(frontiers, hazard_decision)
    filtered = [
        frontier
        for frontier in scored_frontiers
        if frontier.reachable
        and frontier.area_m2 >= min_size
        and frontier.travel_cost <= max_travel_cost
    ]
    return sorted(
        filtered,
        key=lambda frontier: (-frontier.info_gain, frontier.travel_cost, frontier.frontier_id),
    )


def apply_hazard_weighting(
    frontiers: Iterable[FrontierCandidate],
    hazard_decision=None,
) -> List[FrontierCandidate]:
    """Increase travel cost when the robot's fused risk is high."""
    frontiers = list(frontiers)
    if hazard_decision is None:
        return frontiers

    risk_level = float(getattr(hazard_decision, 'risk_level', 0.0))
    if risk_level <= HAZARD_RISK_THRESHOLD:
        return frontiers

    hazard_robot_id = str(getattr(hazard_decision, 'robot_id', ''))
    weighted = []
    for frontier in frontiers:
        if hazard_robot_id and hazard_robot_id != frontier.robot_id:
            weighted.append(frontier)
            continue

        weighted.append(
            FrontierCandidate(
                frontier_id=frontier.frontier_id,
                robot_id=frontier.robot_id,
                area_m2=frontier.area_m2,
                info_gain=frontier.info_gain,
                travel_cost=frontier.travel_cost * HAZARD_TRAVEL_COST_MULTIPLIER,
                reachable=frontier.reachable,
                centroid_x=frontier.centroid_x,
                centroid_y=frontier.centroid_y,
            )
        )
    return weighted
