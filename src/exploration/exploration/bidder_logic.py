from dataclasses import dataclass


@dataclass(frozen=True)
class BidScore:
    utility_score: float
    eta_sec: float
    energy_cost: float


def score_frontier(
    info_gain: float,
    travel_cost: float,
    speed_mps: float,
    energy_rate: float,
) -> BidScore:
    """Compute a stable bid score for a frontier candidate."""
    bounded_speed = max(speed_mps, 0.01)
    eta_sec = travel_cost / bounded_speed
    energy_cost = travel_cost * max(energy_rate, 0.0)
    utility_score = info_gain / (1.0 + travel_cost + energy_cost)
    return BidScore(
        utility_score=utility_score,
        eta_sec=eta_sec,
        energy_cost=energy_cost,
    )
