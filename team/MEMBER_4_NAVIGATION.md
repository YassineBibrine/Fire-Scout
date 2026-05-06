# Member 4: Exploration + Common Utilities Lead

## Scope

- Own frontier exploration and auction logic, plus shared helper utilities used by the runtime packages.

## Package Surface

- `src/exploration/exploration/`
- `src/exploration/launch/`
- `src/exploration/config/`
- `src/exploration/test/`
- `src/common_utils/common_utils/`
- `src/common_utils/config/`
- `src/common_utils/test/`

## Implemented

- Exploration runtime entry points exist for `frontier_detector_node`, `auctioneer_node`, and `bidder_node`.
- Exploration launch files and configs are present for frontier detection and auction coordination.
- `common_utils` provides shared math, geometry, namespace, and QoS helper modules.
- `common_utils` remains a utility-only package with no runtime nodes.
- Both packages include focused test coverage.

## Tests Present

- `src/exploration/test/test_frontier_startup_gate.py`
- `src/exploration/test/test_frontier_output.py`
- `src/exploration/test/test_auction_single_winner.py`
- `src/exploration/test/test_bid_timeout.py`
- `src/common_utils/test/test_math_utils.py`
- `src/common_utils/test/test_geometry_utils.py`
- `src/common_utils/test/test_namespace_utils.py`

## Current Status

- [x] Frontier detection and auction flow are implemented.
- [x] Common utility helpers are implemented and reusable.
- [x] Exploration and common_utils config files are present.
- [x] Test coverage exists for both packages.

## Phase 2 - Hybrid System Tasks 

Hybrid support scope: exploration behavior adapts to fire/human confirmations.

- Update exploration scoring logic so confirmed fire zones are deprioritized for normal exploration and escalated for response workflows.
- Add helper utilities in `common_utils` for hybrid confidence weighting (sensor confidence + vision confidence).
- Add normal-priority tests verifying auction/frontier behavior when fusion decisions mark zones as hazardous.
- Ensure exploration nodes subscribe safely to fusion outputs without creating hard dependencies on response internals.
- Document fallback behavior when camera detections are unavailable but fire sensors still trigger alerts.
