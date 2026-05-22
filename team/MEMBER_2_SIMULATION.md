# Member 2: Simulation Lead

## Scope

- Own the simulation assets, multi-robot spawning, and Gazebo bridge definitions for `/robot1`, `/robot2`, and `/robot3`.

## Package Surface

- `src/simulation/worlds/`
- `src/simulation/models/`
- `src/simulation/launch/`
- `src/simulation/config/`
- `src/simulation/test/`

## Implemented

- The simulation package includes the launch entry points for `sim.launch.py`, `gazebo_ionic.launch.py`, `gz_world.launch.py`, `spawn_robot.launch.py`, `spawn_tb3.launch.py`, `bridge_global.launch.py`, and `bridge_robot.launch.py`.
- Configuration files for bridge topics, robot spawn poses, and physics settings are present.
- The package includes launch and integration tests for namespace handling, bridge topics, clock availability, and spawn behavior.
- The package is focused on assets and launch orchestration rather than a standalone runtime node module.

## Tests Present

- `src/simulation/test/test_bridge_topics.py`
- `src/simulation/test/test_clock_available.py`
- `src/simulation/test/test_lidar_sensor_model.py`
- `src/simulation/test/test_spawn_namespaces.py`
- `src/simulation/test/test_spawn_robot_launch.py`

## Current Status

- [x] Three-robot spawn flow is implemented.
- [x] Per-robot bridge definitions are present.
- [x] Simulation config files are in place.
- [x] Simulation test coverage exists for the main launch behavior.

## Phase 2 - Simulation Tasks

Primary objective: upgrade simulation world and robot models for hybrid fire/human scenarios.

- [ ] Add a camera sensor to `src/simulation/models/*/model.sdf` with pose `0.10 0 0.15 0 0 0`, topic `~/camera/image_raw`, rate 15, and 640x480 RGB8.
- [ ] Add camera bridge entry in `src/simulation/launch/bridge_robot.launch.py` for `/robotX/camera/image_raw` ↔ `gz.msgs.Image` (GZ_TO_ROS).
- [ ] Add a fire entity to `src/simulation/worlds/world_1.sdf` (red/orange box, no physics) at `(3.0, 2.0, 0)` with realistic placement and ignition zones for repeatable test scenes.
- [ ] Add a human entity to `src/simulation/worlds/world_1.sdf` (blue box) at `(-3.0, 4.0, 0)` with multiple rescue scenarios (single victim, multiple victims, blocked path).
- Improve visual/material and collision models in `.sdf` assets so obstacle boundaries and fire zones are more realistic for avoidance testing.
- [ ] Add launch arguments in `src/simulation/launch/sim.launch.py`: `spawn_fire_entities` and `spawn_human_entities` (default true) to enable or disable fire and human scenario packs for CI and demos.
- [ ] Add `mock_camera_inference_node` in `src/testing_tools/testing_tools/` that reads Gazebo entity positions and publishes `VisionDetectionArray`.
- [ ] Add tests: `test_camera_bridge_topic.py` for `/robot1/camera/image_raw` and `test_fire_entity_spawn.py` for fire entity existence.
