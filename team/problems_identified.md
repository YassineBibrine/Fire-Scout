# Problems Identified During Live Simulation

This document summarizes problems observed during live Gazebo/ROS runs of:

```bash
ros2 launch bringup full_system.launch.py
```

The unit and package tests passed, but live simulation exposed runtime integration gaps. Responsibilities below follow the team ownership files in `team/`.

## Summary Table

| Problem | Evidence From Live Runs | Impact | Responsible Owner | Status |
|---|---|---|---|---|---|
| No fused hybrid decision stream | `/robot1/fusion_decision`, `/robot2/fusion_decision`, and `/robot3/fusion_decision` had `0 publishers, 0 messages`. | Phase 2 hybrid behavior is not end-to-end. Member 4 hazard-aware exploration cannot receive real fused risk data in the full stack. | Member 5 for fusion/sensor nodes; Member 6 for launching them in full-system bringup. | RESOLVED — hybrid_pipeline.launch.py now launches fusion_decision_node per robot via robot_stack.launch.py |
| Fusion pipeline is not launched | Full stack launched fire/human detection nodes, but no live `fusion_decision_node`, `sensor_gateway_node`, or sim/real inference fusion chain was present. | Fire/human confirmations cannot drive exploration, response, or safety logic. | Member 6 for orchestration; Member 5 for node implementation. | RESOLVED — sensor_gateway_node, mock_camera_inference_node (sim profile), and fusion_decision_node are all launched by hybrid_pipeline.launch.py |
| SLAM lifecycle manager bond failures | `slam_toolbox_manager_robotX`: `Server slam_toolbox_robotX was unable to be reached after 4.00s by bond` and `Failed to bring up all requested nodes. Aborting bringup.` | Mapping may still publish later, but lifecycle state is unstable and startup health looks degraded. | Member 3. |
| Lidar message filter drops | Examples: `frame 'robot2/lidar' ... queue is full`, `frame 'robot3/lidar' ... queue is full`, and `timestamp ... earlier than all the data in the transform cache`. | SLAM can lag, lose scans, or build maps inconsistently. This can cascade into empty frontiers and inconsistent task generation. | Member 3, with possible Member 2 involvement if Gazebo/bridge timing is the source. |
| RViz shader error | RViz reported `active samplers with a different type refer to the same texture image unit`. | Visualization may render incorrectly or behave inconsistently. Core ROS topics can still run. | Member 6 if RViz config is involved; otherwise environment/GPU-specific. |
| Initial robot health degradation | Health monitor logged `Robot robot1/2/3 is DEGRADED`; later `/coordination/system_health` could become `HEALTHY`. | Startup health state is noisy and can trigger fault supervision even while the stack is still settling. | Member 6, with Member 3 input because health depends on SLAM status. |
| Empty frontier arrays in one live probe | `/coordination/frontiers` published but sample had `frontiers=0`. | Auction and task assignment may not proceed because no candidate frontiers exist. | Likely Member 3 if caused by unstable/absent maps; Member 4 should only investigate if valid maps are present and frontier extraction still returns empty. |
| Auction/task flow absent during one probe window | `/coordination/auction_bids`, `/coordination/auction_result`, and `/coordination/task_assignments` had publishers but no messages during the sampled interval. | Robots may appear idle even though the stack is launched. | Downstream of empty frontiers; likely Member 3 first, Member 4 only if frontier inputs are valid, Member 6 if coordination timing/launch sequencing is implicated. |
| Intermittent map topic gaps | During one probe, `/robot1/map` and `/robot3/map` had no messages. | Frontier detection, map merge, monitoring, and RViz can behave inconsistently. | Member 3. |
| Intermittent camera topic gap | During one probe, `/robot1/camera/image_raw` had a publisher but no sampled messages. | Vision inference/fusion cannot be reliable for that robot. | Member 2 for Gazebo/bridge camera stream; Member 6 if launch timing/config is involved. |
| Intermittent safe velocity gap | During one probe, `/robot2/cmd_vel_safe` had a publisher but no sampled messages. | Gazebo may not receive safe velocity commands for that robot during that interval. | Member 6. | |
| Incident tasks always assigned to detecting robot | `coordination_bridge_node._build_assignment` uses `incident.robot_id` unconditionally. If that robot has a higher-priority active task, `task_executor` rejects the assignment and no robot responds. | Multi-robot load balancing for incident response is non-functional until Phase 3. | Member 6. | |

## Member 4 Status

Member 4's requested Phase 2 work is complete and tested:

- Exploration subscribes to `/robotX/fusion_decision` and does not subscribe directly to `/incidents/fire`.
- High-risk fused decisions multiply matching frontier `travel_cost` by `3.0`.
- Missing fusion decisions keep baseline scoring.
- `common_utils.weighted_confidence(...)` exists and is tested.
- A direct live test confirmed the real `frontier_detector_node` applies the `3.0` travel-cost multiplier when a `FusionDecision` is published.

Member 4 should only revisit frontier logic if a future live run provides stable `/robotX/map` inputs and `/coordination/frontiers` still remains empty or incorrectly scored.

## Recommended Fix Order

1. Member 3: resolve triple TF publisher for odom→base_link (bridge `publish_tf` + `odom_tf_publisher` + `slam_wrapper` all publish same transform — see current open issues).
2. Member 3: stabilize SLAM lifecycle/bond behavior and lidar message filters.
3. Member 3 and Member 2: verify map and camera streams remain steady after startup.
4. Member 6: reduce startup false-degraded health states and review safe velocity output timing.
5. Member 6: review RViz config/environment notes for the shader error.

## Live Probe Notes

The live checks used actual ROS topics after launching the full stack. A previous command-line test failure was caused by sandboxed ROS/DDS networking, so live simulation and probes were rerun with host DDS/network access.

## Resolved Issues

| Problem | Resolution | Date |
|---|---|---|
| No fused hybrid decision stream (0 publishers) | `hybrid_pipeline.launch.py` now launches `fusion_decision_node` per robot via `robot_stack.launch.py` | 2026-06-06 |
| Fusion pipeline not launched | `sensor_gateway_node`, `mock_camera_inference_node` (sim profile), and `fusion_decision_node` are all launched by `hybrid_pipeline.launch.py` | 2026-06-06 |
