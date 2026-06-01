# Member 6: Coordination, Bringup, and Testing Tools Lead

## Scope

- Own full-system orchestration, mission and fault coordination, and dummy tooling for integration safety.

## Package Surface

- `src/coordination/coordination/`
- `src/coordination/launch/`
- `src/coordination/config/`
- `src/coordination/test/`
- `src/bringup/launch/`
- `src/bringup/config/`
- `src/bringup/test/`
- `src/testing_tools/testing_tools/`
- `src/testing_tools/launch/`
- `src/testing_tools/config/`
- `src/testing_tools/test/`

## Implemented

- Coordination runtime entry points exist for mission management, health monitoring, fault supervision, task allocation, task execution, and cmd_vel safety.
- Bringup launch files are present for the full system, global stack, and robot stack composition.
- Bringup config files are present for parameters, namespace mapping, Nav2, and RViz.
- Testing tools provide dummy publishers, a fault injector, a frontier dummy publisher, and a namespace lint node.
- Testing tools launchers and configs are present for integration and fault scenarios.

## Tests Present

- `src/coordination/test/test_heartbeat_timeout.py`
- `src/coordination/test/test_fault_reassignment.py`
- `src/coordination/test/test_task_allocation.py`
- `src/coordination/test/test_task_executor_bootstrap.py`
- `src/coordination/test/test_cmd_vel_safety.py`
- `src/bringup/test/test_full_launch_smoke.py`
- `src/bringup/test/test_robot_stack_launch_args.py`
- `src/bringup/test/test_rviz_config.py`
- `src/testing_tools/test/test_dummy_interfaces.py`

## Current Status

- [x] Full system launch entry point is in place.
- [x] Coordination logic and safety nodes are implemented.
- [x] Dummy integration tooling is implemented.
- [x] Core bringup and testing tools configs are present.
- [ ] There is no dedicated bringup namespace-isolation test file yet.

## Phase 2 — Obstacle Handling Improvements 

Problem: robots detect obstacles but often stop and remain stopped for a long time (or never resume). We need faster, more reliable obstacle detection-to-avoidance behavior so robots avoid obstacles rather than blocking indefinitely.

Planned tasks (owner: Member 6)

- Reproduce obstacle stop: script a deterministic simulation scenario (use `testing_tools` dummy publishers and `simulation` spawn) that reliably triggers the stop-and-stall behavior.
- Add `cmd_vel` decision logging: instrument `src/coordination/coordination/cmd_vel_safety_node.py` (or equivalent node) to emit structured logs and metrics when obstacle detections occur and when the node chooses to stop, wait, or override commands.
- Create integration test: add a CI-style integration test that reproduces the failure case in-simulation and asserts recovery within a bounded time.
- Implement non-blocking avoidance: change the safety logic to prefer short avoidance maneuvers (temporary lateral/backwards + rotate) or delegate to a local planner (DWA/local_planner) rather than full stop-and-wait. Prefer reactive, bounded maneuvers with a clear timeout before entering a hold state.
- Tune safety thresholds: reduce stop timeouts, add a max-hold counter, and expose parameters for distance/time thresholds in `src/bringup/config/namespace_map.yaml` or a `coordination` params file so teams can iterate quickly.
- Add monitoring metrics & alerts: track obstacle-handling latency and stop durations in `monitoring/metrics_exporter_node.py` and raise alarms for long-held stops so CI/ops notice regressions.
- Update bringup configs & docs: add a `phase2` section in `src/bringup/config/params.yaml` and update this `MEMBER_6_BRINGUP.md` with run instructions and the integration test location.

## Phase 2 - Hybrid System Tasks 

Hybrid target: production-grade orchestration for Jetson + sensors + ROS 2 fusion.

- [x] Add `sensor_gateway_node`, `camera_inference_node`, and `fusion_decision_node` per robot in `full_system.launch.py` (TimerAction 8s offset consistent with robots).
- [x] Add `launch_profile` arg in `full_system.launch.py` (`sim`, `robot`, `debug`) with sim using `mock_camera_inference_node` and robot using real inference node.
- [x] In `health_monitor_node.py`, track `/robotX/fusion_decision` liveness; emit NodeStatus DEGRADED when silent > 5s with error `camera_sensor_timeout:robotX`.
- [x] If all three robots are in `camera_sensor_timeout`, transition `mission_manager` to SAFE_STOP state.
- [x] Extend `cmd_vel_safety_node.py` to subscribe to `/robotX/fusion_decision` and reduce max_linear_speed to 0.1 when `risk_level > 0.8`.
- [x] Allow critical-task speed policy passthrough when `recommended_action` is `SUPPRESS` or `RESCUE`, while keeping close-obstacle avoidance active.
- [x] Add tests: `test_hybrid_failover_camera_timeout.py`, `test_hybrid_failover_both_timeout.py`, `test_cmd_vel_safety_risk_level.py`, `test_full_launch_hybrid_sim_profile.py`.

Run profiles:

```bash
ros2 launch bringup full_system.launch.py launch_profile:=sim
ros2 launch bringup full_system.launch.py launch_profile:=robot model_path:=/path/to/model.pt
ros2 launch bringup full_system.launch.py launch_profile:=debug
```
