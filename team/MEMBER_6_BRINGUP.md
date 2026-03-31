# Member 6: Coordination, Bringup, and Testing Tools Lead

## Package Ownership
- `src/coordination`
- `src/bringup`
- `src/testing_tools`

## Responsibility
Own full-system orchestration, mission/fault coordination, and dummy tooling that enables parallel development and integration safety.

## Files and Folders
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

## Implementation Tasks (Coordination)
- [ ] Implement mission manager runtime node
- [ ] Implement health monitor runtime node
- [ ] Implement fault supervisor runtime node
- [ ] Implement task allocator runtime node

## Implementation Tasks (Bringup)
- [ ] Maintain `full_system.launch.py` as the single orchestration entrypoint
- [ ] Maintain global and per-robot stack launch composition
- [ ] Maintain namespace mapping and bringup parameters

## Implementation Tasks (Testing Tools)
- [ ] Maintain dummy publishers (`scan`, `odom`, `camera`, `heartbeat`)
- [ ] Maintain fault injector and frontier dummy publisher
- [ ] Maintain namespace lint node and integration dummy launchers

## Configuration Tasks
- [ ] Maintain coordination policies (`mission_policy.yaml`, `fault_policy.yaml`, `allocator.yaml`)
- [ ] Maintain bringup configs (`params.yaml`, `namespace_map.yaml`, `firescout_viz.rviz`)
- [ ] Maintain testing_tools configs (`dummy_rates.yaml`, `fault_scenarios.yaml`)

## Testing Tasks
- [ ] Maintain coordination tests (`test_heartbeat_timeout.py`, `test_fault_reassignment.py`, `test_task_allocation.py`)
- [ ] Maintain bringup tests (`test_full_launch_smoke.py`, `test_namespace_isolation.py`)
- [ ] Maintain testing_tools tests (`test_dummy_interfaces.py`)

## Done Criteria
- [ ] Full system launch is stable with 3 robots
- [ ] Weekly integration tests can run with dummy tools
- [ ] Fault handling and reassignment behavior is test-backed
- [ ] Coordination/bringup/testing tools tests pass in CI
