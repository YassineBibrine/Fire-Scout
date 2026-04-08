# Member 4: Exploration + Common Utilities Lead

## Package Ownership
- `src/exploration`
- `src/common_utils`

## Responsibility
Own frontier exploration and auction logic, plus shared helper utilities used by teams without cross-importing runtime packages.

## Files and Folders
- `src/exploration/exploration/`
- `src/exploration/launch/`
- `src/exploration/config/`
- `src/exploration/test/`
- `src/common_utils/common_utils/`
- `src/common_utils/config/`
- `src/common_utils/test/`

## Implementation Tasks (Exploration)
- [x] Implement frontier detector runtime node
- [x] Implement auctioneer runtime node
- [x] Implement bidder runtime node for per-robot participation
- [x] Keep global and per-robot exploration launch files aligned

## Implementation Tasks (Common Utils)
- [x] Maintain shared geometry/math helper functions
- [x] Maintain namespace helper utilities
- [x] Maintain QoS profile helper definitions
- [x] Ensure package contains no ROS runtime nodes

## Configuration Tasks
- [x] Maintain `exploration/config/frontier.yaml`
- [x] Maintain `exploration/config/auction.yaml`
- [x] Maintain `common_utils/config/defaults.yaml`

## Testing Tasks
- [x] Maintain exploration tests (`test_frontier_output.py`, `test_auction_single_winner.py`, `test_bid_timeout.py`)
- [x] Maintain common_utils tests (`test_math_utils.py`, `test_geometry_utils.py`, `test_namespace_utils.py`)

## Done Criteria
- [x] Exploration produces deterministic assignments
- [x] Auction rules are documented and tested
- [x] common_utils remains dependency-safe and reusable
- [ ] Exploration/common_utils tests pass in CI
