# Member 2: Simulation (Gazebo Ionic) & TurtleBot3

## Responsibility
Build and maintain the Gazebo Ionic simulation environment including worlds, TurtleBot3 integration, and simulation-specific launch files.

## Primary Files
- `src/simulation/worlds/*.world`
- `src/simulation/models/` (URDF/SDF files)
- `src/simulation/launch/*.launch.py`
- `src/simulation/CMakeLists.txt`
- `src/simulation/package.xml`

## Directory Structure
```
simulation/
├── worlds/              # Gazebo world files (.world)
│   └── firescout_env.world
├── models/              # Robot URDF/SDF and meshes
│   ├── firescout_robot/
│   └── obstacles/
└── launch/
  ├── gazebo_ionic.launch.py
  └── spawn_turtlebot3.launch.py
```

## Tasks

### Phase 1: Environment Setup
- [ ] Create Gazebo world file (`firescout_env.world`) with:
  - Terrain/ground plane
  - Example buildings/obstacles
  - Lighting and physics configuration
- [ ] Configure physics engine (gravity, friction, etc.)

### Phase 2: Robot Model
- [ ] Integrate TurtleBot3 model set (burger/waffle/waffle_pi)
- [ ] Define multi-robot spawn strategy with namespaces
- [ ] Confirm LiDAR and IMU topics match SLAM and Nav2 expectations
- [ ] Add any Fire-Scout-specific sensor/plugin extensions on top of TurtleBot3 base

### Phase 3: Launch Files
- [ ] Create `gazebo_ionic.launch.py` to start Gazebo Ionic (`gz sim`) with the world
- [ ] Create `spawn_turtlebot3.launch.py` to spawn one or more TurtleBot3 robots
- [ ] Add configurable parameters (number of robots, initial poses, etc.)

### Phase 4: Testing
- [ ] Test simulation launch: `ros2 launch simulation gazebo_ionic.launch.py`
- [ ] Verify robot spawning and sensor output
- [ ] Check TF (transform) tree

## Key Notes
- Uses `ament_cmake` because Gazebo assets need to be installed to `share/`
- Runtime stack: `ros_gz_sim` + `ros_gz_bridge` + `turtlebot3_description`
- `CMakeLists.txt` includes install directive for worlds, models, launch:
  ```cmake
  install(DIRECTORY worlds models launch
    DESTINATION share/${PROJECT_NAME}
  )
  ```
- Coordinate with Member 1 for sensor message types

## Build Command
```bash
colcon build --packages-select simulation
```

## Success Criteria
✓ Gazebo world launches without errors
✓ Robots spawn correctly in simulation
✓ Sensors publish data to ROS topics
✓ Can visualize in RViz2
