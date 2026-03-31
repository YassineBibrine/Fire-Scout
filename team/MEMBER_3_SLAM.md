# Member 3: Mapping + Monitoring Lead

## Package Ownership
- `src/mapping`
- `src/monitoring`

## Responsibility
Own SLAM, map merging, TF map policy, and system observability (latency/rate metrics).

## Files and Folders
- `src/mapping/mapping/`
- `src/mapping/launch/`
- `src/mapping/config/`
- `src/mapping/test/`
- `src/monitoring/monitoring/`
- `src/monitoring/launch/`
- `src/monitoring/config/`
- `src/monitoring/test/`

## Implementation Tasks (Mapping)
- [ ] Implement per-robot SLAM runtime nodes and wrappers
- [ ] Implement map merge runtime node and status publisher
- [ ] Maintain TF policy from merged map to per-robot map frames
- [ ] Keep mapping launch files aligned with bringup robot/global stacks

## Implementation Tasks (Monitoring)
- [ ] Implement topic-rate monitoring node
- [ ] Implement latency monitoring node
- [ ] Implement metrics exporter node
- [ ] Define monitored topics and threshold policies

## Configuration Tasks
- [ ] Maintain `mapping/config/slam_toolbox_robot.yaml`
- [ ] Maintain `mapping/config/map_merge.yaml`
- [ ] Maintain `mapping/config/tf_policy.yaml`
- [ ] Maintain `monitoring/config/monitor_topics.yaml`
- [ ] Maintain `monitoring/config/thresholds.yaml`

## Testing Tasks
- [ ] Maintain mapping tests (`test_slam_topics.py`, `test_map_merge_output.py`, `test_tf_consistency.py`)
- [ ] Maintain monitoring tests (`test_topic_rate_alarm.py`, `test_latency_alarm.py`)

## Done Criteria
- [ ] Merged map topic is stable and documented
- [ ] TF map policy has no frame conflicts
- [ ] Monitoring alarms trigger correctly
- [ ] Mapping and monitoring tests pass in CI
