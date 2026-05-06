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
