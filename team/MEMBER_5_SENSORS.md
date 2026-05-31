# Member 5: Response and Incident Handling Lead

## Scope

- Own fire and human detection plus incident prioritization, including rescue and suppression planning interfaces.

## Package Surface

- `src/response/response/`
- `src/response/launch/`
- `src/response/config/`
- `src/response/test/`

## Implemented

- Runtime entry points exist for `sensor_gateway_node`, `camera_inference_node`, `fusion_decision_node`, `fire_detection_node`, `human_detection_node`, `suppression_planning_node`, `rescue_planning_node`, and `coordination_bridge_node`.
- Launch files are present for per-robot detection and global incident handling.
- Config files are present for fire detection, human detection, and prioritization behavior.
- Test coverage exists for the detection pipelines and incident priority logic.

## Tests Present

- `src/response/test/test_fire_detection_pipeline.py`
- `src/response/test/test_human_detection_pipeline.py`
- `src/response/test/test_incident_priority.py`
- `src/response/test/test_sensor_gateway_output.py`
- `src/response/test/test_fusion_decision_sensor_only.py`
- `src/response/test/test_fusion_decision_confirmed.py`
- `src/response/test/test_fusion_temporal_filter.py`
- `src/response/test/test_multi_incident_priority.py`
- `src/response/test/test_coordination_bridge_output.py`
- `src/response/test/test_smoke_unittest.py`

## Current Status

- [x] Fire detection is implemented.
- [x] Human detection is implemented.
- [x] Suppression and rescue planning entry points are implemented.
- [x] Priority and pipeline tests are present.
- [ ] There is no dedicated test file yet for the planning nodes themselves.

## Phase 2 - Hybrid System Tasks 

Hybrid target: high-confidence fire/human confirmation and mission-priority decisions.

- [x] Implement `sensor_gateway_node.py` to publish `/robotX/fire_sensor_alert` from `/robotX/esp32/sensors` and add entry point in `setup.py`.
- [x] Implement `camera_inference_node.py` subscribing to `/robotX/camera/image_raw`, with params `model_path` and `confidence_threshold`, publishing `/robotX/camera_detections`, and add entry point.
- [x] Implement `fusion_decision_node.py` subscribing to fire sensor + camera detections, publishing `/robotX/fusion_decision` with 2-of-2 temporal confirmation within 3 seconds.
- [x] Upgrade `fire_detection_node.py` to publish `FireDetection` only when `fusion_decision.fire_confirmed == true`.
- [x] Add conflict resolution in `rescue_planning_node.py` (human > fire, then confidence, then robot_id lexicographic).
- [x] Add tests: `test_sensor_gateway_output.py`, `test_fusion_decision_sensor_only.py`, `test_fusion_decision_confirmed.py`, `test_fusion_temporal_filter.py`, `test_multi_incident_priority.py`.
- [x] Integrate with `coordination` task assignment so hybrid-confirmed incidents trigger actionable `TaskAssignment` outputs with bounded response latency.

Robot profile inference:

```bash
ros2 launch bringup full_system.launch.py launch_profile:=robot model_path:=/path/to/model.pt
```

The robot profile requires an Ultralytics YOLO model. The `debug` profile may use the explicit brightness stub when no model path is supplied.
