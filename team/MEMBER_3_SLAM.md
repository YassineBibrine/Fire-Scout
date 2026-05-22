# Member 3: Mapping + Monitoring Lead

## Scope

- Own SLAM, map merging, TF map policy, and observability for latency and topic-rate metrics.

## Package Surface

- `src/mapping/mapping/`
- `src/mapping/launch/`
- `src/mapping/config/`
- `src/mapping/test/`
- `src/monitoring/monitoring/`
- `src/monitoring/launch/`
- `src/monitoring/config/`
- `src/monitoring/test/`

## Implemented

- Mapping runtime entry points exist for `lidar_demux_node`, `slam_wrapper_node`, and `map_merge_node`.
- Mapping launch and config files are present for per-robot SLAM, map merging, and TF policy.
- Monitoring runtime entry points exist for `topic_rate_monitor_node`, `latency_monitor_node`, and `metrics_exporter_node`.
- Monitoring launch and config files are present for topic selection and threshold policy.
- Test coverage exists for both mapping and monitoring behavior.

## Tests Present

- `src/mapping/test/test_slam_topics.py`
- `src/mapping/test/test_slam_wrapper_tf.py`
- `src/mapping/test/test_tf_consistency.py`
- `src/mapping/test/test_map_merge_validation.py`
- `src/mapping/test/test_map_merge_output.py`
- `src/monitoring/test/test_topic_rate_alarm.py`
- `src/monitoring/test/test_latency_alarm.py`

## Current Status

- [x] Per-robot SLAM and map merge runtime pieces are implemented.
- [x] TF and map policy configs are present.
- [x] Monitoring nodes and threshold configs are present.
- [x] Mapping and monitoring tests exist.
- [ ] `metrics_exporter_node` does not yet have a dedicated test file.

## Phase 2 - Hybrid System Tasks 

Hybrid support scope: mapping and monitoring support for sensor+vision fusion reliability.

- Add map annotations or lightweight zone tagging for high-risk fire areas to help fusion context.
- Extend monitoring topic policies to include hybrid health metrics (sensor heartbeat rate, camera inference latency).
- Add one monitoring test for hybrid timing alarms (for example, delayed camera detections).
- Validate TF consistency for camera frames used by Jetson inference outputs.
- Document expected map/fusion topic dependencies so response and coordination teams consume consistent data.
## Phase 2 - Hybrid System Tasks 

Hybrid support scope: mapping and monitoring support for sensor+vision fusion reliability.

- [ ] Add camera static TF in `src/mapping/launch/slam_robot.launch.py` for each robot (parent `robotX/base_link`, child `robotX/camera`, translation `0.10 0 0.15`, rotation `0 0 0`).
- [ ] Update `src/mapping/config/tf_policy.yaml` to document the camera frame (publisher: `slam_robot.launch.py` static_transform_publisher, rate: static).
- [ ] Add monitor topics in `src/monitoring/config/monitor_topics.yaml` for camera, fire_sensor_alert, and fusion_decision with expected rates (15.0, 5.0, 2.0 per robot).
- [ ] Add latency thresholds in `src/monitoring/config/thresholds.yaml` (`camera_max_latency_ms: 200.0`, `sensor_alert_max_latency_ms: 500.0`).
- [ ] Update `metrics_exporter_node` to emit CRITICAL when both `/robotX/fire_sensor_alert` and `/robotX/camera/image_raw` are silent for > 5 seconds.
- [ ] Add tests: `test_metrics_exporter.py`, `test_tf_camera_consistency.py`, and `test_hybrid_timing_alarm.py`.
