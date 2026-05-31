# Phase 2 Task Checklist

Tracking table for Phase 2 hybrid solution work.

Legend:
- Status: `Not Started`, `In Progress`, `Blocked`, `Done`
- Priority: `Hard`, `Normal`, `Simulation`

| Owner | Priority | Task | Status | Deadline |
|---|---|---|---|---|
| Member 1 (Interfaces) | Hard | Define FireSensorAlert.msg fields | Done | 2026-05-12 |
| Member 1 (Interfaces) | Hard | Define VisionDetectionArray.msg + Detection struct | Done | 2026-05-12 |
| Member 1 (Interfaces) | Hard | Define FusionDecision.msg fields | Done | 2026-05-12 |
| Member 1 (Interfaces) | Hard | Add migration note for FireDetection in interface_contract.yaml | Done | 2026-05-13 |
| Member 1 (Interfaces) | Hard | Document QoS policies for hybrid topics | Done | 2026-05-13 |
| Member 1 (Interfaces) | Hard | Add schema validation tests for hybrid messages | Done | 2026-05-15 |
| Member 2 (Simulation) | Simulation | Add camera sensor to robot model.sdf | Done | 2026-05-13 |
| Member 2 (Simulation) | Simulation | Add camera ros_gz_bridge entry in bridge_robot.launch.py | Done | 2026-05-13 |
| Member 2 (Simulation) | Simulation | Add fire entity in world_1.sdf | Done | 2026-05-14 |
| Member 2 (Simulation) | Simulation | Add human entity in world_1.sdf | Done | 2026-05-14 |
| Member 2 (Simulation) | Simulation | Add sim.launch.py args spawn_fire_entities/spawn_human_entities | Done | 2026-05-15 |
| Member 2 (Simulation) | Simulation | Add mock_camera_inference_node in testing_tools | Done | 2026-05-16 |
| Member 2 (Simulation) | Simulation | Add tests: test_camera_bridge_topic.py + test_fire_entity_spawn.py | Done | 2026-05-16 |
| Member 3 (Mapping/Monitoring) | Normal | Add camera static TF in slam_robot.launch.py | Done | 2026-05-14 |
| Member 3 (Mapping/Monitoring) | Normal | Update tf_policy.yaml for camera frame | Done | 2026-05-14 |
| Member 3 (Mapping/Monitoring) | Normal | Add monitor_topics.yaml entries for camera/sensor/fusion | Done | 2026-05-15 |
| Member 3 (Mapping/Monitoring) | Normal | Add thresholds.yaml camera/sensor latency limits | Done | 2026-05-15 |
| Member 3 (Mapping/Monitoring) | Normal | Update metrics_exporter_node critical rule for dual silence | Done | 2026-05-16 |
| Member 3 (Mapping/Monitoring) | Normal | Add tests: metrics_exporter, tf_camera_consistency, hybrid_timing_alarm | Done | 2026-05-18 |
| Member 4 (Exploration/Utils) | Normal | Subscribe frontier scoring to fusion_decision only | Done | 2026-05-14 |
| Member 4 (Exploration/Utils) | Normal | Deprioritize frontiers when risk_level > 0.7 | Done | 2026-05-15 |
| Member 4 (Exploration/Utils) | Normal | Add weighted_confidence helper in common_utils | Done | 2026-05-15 |
| Member 4 (Exploration/Utils) | Normal | Add tests: hazard_aware_frontier_scoring + weighted_confidence_util | Done | 2026-05-17 |
| Member 5 (Response) | Hard | Implement sensor_gateway_node | Done | 2026-05-15 |
| Member 5 (Response) | Hard | Implement camera_inference_node | Done | 2026-05-16 |
| Member 5 (Response) | Hard | Implement fusion_decision_node | Done | 2026-05-17 |
| Member 5 (Response) | Hard | Upgrade fire_detection_node to consume fusion_decision | Done | 2026-05-17 |
| Member 5 (Response) | Hard | Add conflict resolution in rescue_planning_node | Done | 2026-05-18 |
| Member 5 (Response) | Hard | Add tests for fusion and multi-incident priority | Done | 2026-05-19 |
| Member 6 (Coordination/Bringup) | Hard | Add hybrid nodes per robot in full_system.launch.py | Done | 2026-05-15 |
| Member 6 (Coordination/Bringup) | Hard | Add launch_profile sim/robot/debug behavior | Done | 2026-05-16 |
| Member 6 (Coordination/Bringup) | Hard | Add fusion_decision liveness checks and degraded status | Done | 2026-05-17 |
| Member 6 (Coordination/Bringup) | Hard | SAFE_STOP when all robots timed out | Done | 2026-05-18 |
| Member 6 (Coordination/Bringup) | Hard | Extend cmd_vel_safety for risk_level and bounded critical-task passthrough | Done | 2026-05-19 |
| Member 6 (Coordination/Bringup) | Hard | Add hybrid failover and launch profile tests | Done | 2026-05-20 |

## Coordination Milestones

| Milestone | Owner(s) | Status | Deadline |
|---|---|---|---|
| Phase 2 interface freeze | Member 1 + Member 6 | Done | 2026-05-12 |
| Simulation scenario ready (fire + human + camera) | Member 2 | Done | 2026-05-16 |
| Hybrid integration dry run | Members 2, 5, 6 | Done | 2026-05-19 |
| Full Phase 2 system validation | All members | In Progress | 2026-05-22 |
