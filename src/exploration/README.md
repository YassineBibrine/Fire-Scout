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
3. Keep only frontiers with `travel_cost <= frontier_max_travel_cost`.
4. Sort by higher `info_gain`, then lower `travel_cost`, then `frontier_id`.

## Tests Covering Rules

- `test_frontier_output.py`
- `test_auction_single_winner.py`
- `test_bid_timeout.py`
