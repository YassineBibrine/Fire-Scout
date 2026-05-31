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

- [x] Update frontier scoring to subscribe only to `/robotX/fusion_decision` and never directly to `/incidents/fire`.
- [x] When `fusion_decision.risk_level > 0.7` for a frontier zone, multiply travel_cost by `3.0`.
- [x] Add `weighted_confidence(sensor_conf, vision_conf, sensor_weight=0.6, vision_weight=0.4)` in `common_utils`.
- [x] Add tests: `test_hazard_aware_frontier_scoring.py` and `test_weighted_confidence_util.py`.
- [x] Document fallback behavior when fusion decisions are unavailable (skip hazard weighting and keep baseline scoring).
