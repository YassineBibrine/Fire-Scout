# Member 2: Simulation Lead (Gazebo Ionic + TurtleBot3)

## Package Ownership
- `src/simulation`

## Responsibility
Own simulation assets, multi-robot spawning, and Gazebo bridge definitions for `/robot1`, `/robot2`, `/robot3`.

## Files and Folders
- `src/simulation/worlds/`
- `src/simulation/models/`
- `src/simulation/launch/`
- `src/simulation/config/`
- `src/simulation/test/`
- `src/simulation/CMakeLists.txt`
- `src/simulation/package.xml`

## Implementation Tasks
- [ ] Maintain Gazebo world files and robot model assets
- [ ] Maintain spawn launch with deterministic namespace behavior
- [ ] Maintain bridge launch with explicit per-robot topic mapping
- [ ] Keep `gazebo_ionic.launch.py`, `gz_world.launch.py`, and `spawn_robot.launch.py` aligned
- [ ] Ensure clock and simulation settings support all other stacks

## Configuration Tasks
- [ ] Maintain `config/bridge_topics_robot.yaml`
- [ ] Maintain `config/robot_spawn_poses.yaml`
- [ ] Maintain `config/sim_physics.yaml`

## Testing Tasks
- [ ] Maintain `test/test_spawn_namespaces.py`
- [ ] Maintain `test/test_bridge_topics.py`
- [ ] Maintain `test/test_clock_available.py`

## Done Criteria
- [ ] 3 robots spawn with clean namespaces
- [ ] Bridged topics are available for all robots
- [ ] Simulation tests pass in CI
- [ ] No TF/topic collisions caused by simulation assets
