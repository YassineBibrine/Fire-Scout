# Exploration Package Rules

## Auction Rules

The auction winner selection in `exploration.auction_logic.select_winner` is deterministic and follows this order:

1. Exclude bids with `eta_sec > auction_timeout_sec`.
2. If an eligible robot set is provided, exclude bids whose `robot_id` is not eligible.
3. Choose the bid with the maximum `utility_score`.
4. Break ties by lower `eta_sec`.
5. Break remaining ties by lower `energy_cost`.
6. Break remaining ties by lexicographically smaller `robot_id`.

This guarantees stable output for the same set of bids and timeout.

## Frontier Ranking Rules

Frontier selection in `exploration.frontier_logic.select_frontiers` is deterministic:

1. Keep only `reachable` frontiers.
2. Keep only frontiers with `area_m2 >= frontier_min_size`.
3. If a `/robotX/fusion_decision` message is available and `risk_level > 0.7`, multiply travel cost for that robot's frontiers by `3.0`.
4. Keep only frontiers with `travel_cost <= frontier_max_travel_cost`.
5. Sort by higher `info_gain`, then lower `travel_cost`, then `frontier_id`.

Frontier detection consumes fused hybrid decisions only from `/robotX/fusion_decision`; it does not subscribe directly to `/incidents/fire`. When no fusion decision has arrived, hazard weighting is skipped and baseline frontier scoring is preserved.

## Tests Covering Rules

- `test_frontier_output.py`
- `test_hazard_aware_frontier_scoring.py`
- `test_auction_single_winner.py`
- `test_bid_timeout.py`
