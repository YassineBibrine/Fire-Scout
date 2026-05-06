# Member 5: Response and Incident Handling Lead

## Scope

- Own fire and human detection plus incident prioritization, including rescue and suppression planning interfaces.

## Package Surface

- `src/response/response/`
- `src/response/launch/`
- `src/response/config/`
- `src/response/test/`

## Implemented

- Runtime entry points exist for `fire_detection_node`, `human_detection_node`, `suppression_planning_node`, and `rescue_planning_node`.
- Launch files are present for per-robot detection and global incident handling.
- Config files are present for fire detection, human detection, and prioritization behavior.
- Test coverage exists for the detection pipelines and incident priority logic.

## Tests Present

- `src/response/test/test_fire_detection_pipeline.py`
- `src/response/test/test_human_detection_pipeline.py`
- `src/response/test/test_incident_priority.py`
- `src/response/test/test_smoke_unittest.py`

## Current Status

- [x] Fire detection is implemented.
- [x] Human detection is implemented.
- [x] Suppression and rescue planning entry points are implemented.
- [x] Priority and pipeline tests are present.
- [ ] There is no dedicated test file yet for the planning nodes themselves.

## Phase 2 - Hybrid System Tasks 

Hybrid target: high-confidence fire/human confirmation and mission-priority decisions.

- Implement robust fusion-side response gating:
	- sensor-only fire alert -> preliminary incident
	- sensor+vision agreement -> confirmed incident
	- human+confirmed fire -> highest-priority rescue task
- Add temporal and confidence filters to reduce false positives from camera-only detections.
- Add dedicated planning-node tests for rescue/suppression branching under hybrid inputs.
- Add conflict-resolution logic for simultaneous incidents across robots and ensure deterministic priority output.
- Integrate with `coordination` task assignment so hybrid-confirmed incidents trigger actionable `TaskAssignment` outputs with bounded response latency.
