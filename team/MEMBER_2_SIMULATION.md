# Member 2: Simulation & Gazebo Environment

## Responsibility
Build and maintain the Gazebo simulation environment including worlds, robot models, and simulation-specific launch files.

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
    ├── gazebo.launch.py
    └── spawn_robots.launch.py
```

## Tasks

### Phase 1: Environment Setup
- [ ] Create Gazebo world file (`firescout_env.world`) with:
  - Terrain/ground plane
  - Example buildings/obstacles
  - Lighting and physics configuration
- [ ] Configure physics engine (gravity, friction, etc.)

### Phase 2: Robot Model
- [ ] Create multi-robot URDF with:
  - Base frame and geometry
  - LiDAR sensor
  - IMU sensor
  - Camera (optional)
- [ ] Add collision meshes
- [ ] Define sensor plugins for Gazebo

### Phase 3: Launch Files
- [ ] Create `gazebo.launch.py` to start Gazebo with the world
- [ ] Create `spawn_robots.launch.py` to spawn one or more robots
- [ ] Add configurable parameters (number of robots, initial poses, etc.)

### Phase 4: Testing
- [ ] Test simulation launch: `ros2 launch simulation gazebo.launch.py`
- [ ] Verify robot spawning and sensor output
- [ ] Check TF (transform) tree

## Key Notes
- Uses `ament_cmake` because Gazebo assets need to be installed to `share/`
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
