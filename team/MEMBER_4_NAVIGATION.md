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
- [ ] Implement frontier detector runtime node
- [ ] Implement auctioneer runtime node
- [ ] Implement bidder runtime node for per-robot participation
- [ ] Keep global and per-robot exploration launch files aligned

## Implementation Tasks (Common Utils)
- [ ] Maintain shared geometry/math helper functions
- [ ] Maintain namespace helper utilities
- [ ] Maintain QoS profile helper definitions
- [ ] Ensure package contains no ROS runtime nodes

## Configuration Tasks
- [ ] Maintain `exploration/config/frontier.yaml`
- [ ] Maintain `exploration/config/auction.yaml`
- [ ] Maintain `common_utils/config/defaults.yaml`

## Testing Tasks
- [ ] Maintain exploration tests (`test_frontier_output.py`, `test_auction_single_winner.py`, `test_bid_timeout.py`)
- [ ] Maintain common_utils tests (`test_math_utils.py`, `test_geometry_utils.py`, `test_namespace_utils.py`)

## Done Criteria
- [ ] Exploration produces deterministic assignments
- [ ] Auction rules are documented and tested
- [ ] common_utils remains dependency-safe and reusable
- [ ] Exploration/common_utils tests pass in CI
