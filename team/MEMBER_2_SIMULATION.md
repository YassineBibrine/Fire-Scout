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

- Add fire entities in world files (`src/simulation/worlds/*.sdf`) with realistic placement and ignition zones for repeatable test scenes.
- Add human entities in world files (`src/simulation/worlds/*.sdf`) with multiple rescue scenarios (single victim, multiple victims, blocked path).
- Enhance robot model `.sdf` design in `src/simulation/models/` to improve sensor mounting realism (camera frame, lidar frame, optional thermal mount points).
- Improve visual/material and collision models in `.sdf` assets so obstacle boundaries and fire zones are more realistic for avoidance testing.
- Add simulation launch arguments to enable or disable fire and human scenario packs for CI and demos.
- Add/extend tests to validate that fire and human entities are spawned correctly and namespaced topics remain collision-free.
