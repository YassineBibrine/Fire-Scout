# Member 6: System Integration & Bringup

## Responsibility
Coordinate all system components through launch files and configuration, ensuring smooth integration of all Fire-Scout subsystems.

## Primary Files
- `src/bringup/launch/` (main system launch files)
  - `full_system.launch.py` (main entry point)
  - `simulation.launch.py` (simulation mode)
  - `real_robots.launch.py` (hardware mode)
- `src/bringup/setup.py` (properly configured)
- `src/bringup/package.xml`

## Tasks

### Phase 1: Master Launch System
- [ ] Create hierarchical launch structure:
  ```
  full_system.launch.py (main entry point)
  ├── simulation.launch.py
  │   ├── gazebo_ionic.launch.py (from Member 2)
  │   ├── all_sensors.launch.py (from Member 5)
  │   └── slam.launch.py (from Member 3)
  ├── real_robots.launch.py
  │   ├── all_sensors.launch.py (from Member 5)
  │   ├── slam.launch.py (from Member 3)
  │   └── robot_drivers.launch.py
  └── nav2_launch.py (from Member 4)
  ```

### Phase 2: Full System Launch
- [ ] Implement `full_system.launch.py`:
  - Accept arguments: `simulation:=true/false`, `num_robots:=N`, `headless:=true/false`
  - Launch in correct order (interfaces first, then simulation/drivers, then SLAM, then Nav2)
  - Create RViz configuration for visualization
  - Handle multi-robot namespace setup

### Phase 3: Simulation Mode
- [ ] Create `simulation.launch.py`:
  - Launch Gazebo world (Member 2)
  - Spawn robots
  - Start SLAM (Member 3)
  - Start Navigation (Member 4)
  - No hardware drivers

### Phase 4: Real Robot Mode
- [ ] Create `real_robots.launch.py`:
  - Load robot hardware drivers (Member 5)
  - Configure for multi-robot operation
  - Setup parameters and configs
  - Health monitoring nodes

### Phase 5: RViz Configuration
- [ ] Create RViz config file: `config/firescout_viz.rviz`
  - Display map from SLAM
  - Show planned path from Nav2
  - Visualize sensor data (scans, IMU, camera)
  - Show TF tree
  - Multi-robot display with different colors

### Phase 6: Configuration Management
- [ ] Create centralized parameter server config
- [ ] Environment-specific configs (simulation vs real)
- [ ] Robot-specific configs for multi-robot setup
- [ ] Documentation for all configurable parameters

### Phase 7: Testing & Validation
- [ ] Full system integration test (all components together)
- [ ] Multi-robot coordination tests
- [ ] Failure mode handling
- [ ] Performance profiling
- [ ] Documentation and README

## Package Structure
```
bringup/
├── launch/
│   ├── full_system.launch.py (main entry)
│   ├── simulation.launch.py
│   ├── real_robots.launch.py
│   ├── gazebo_ionic.launch.py (includes from Member 2)
│   ├── slam.launch.py (includes from Member 3)
│   ├── nav2.launch.py (includes from Member 4)
│   └── sensors.launch.py (includes from Member 5)
├── config/
│   ├── firescout_viz.rviz
│   ├── params.yaml
│   └── robots/
│       ├── robot1_params.yaml
│       └── robot2_params.yaml
├── setup.py (with launch file data_files configured)
└── package.xml
```

## Key Configuration: setup.py
```python
data_files=[
    ('share/ament_index/resource_index/packages',
        ['resource/bringup']),
    ('share/bringup', ['package.xml']),
    ('share/bringup/launch', glob('launch/*.launch.py')),
    ('share/bringup/config', glob('config/*.rviz')),
    ('share/bringup/config', glob('config/*.yaml')),
]
```

## Launch Commands

### Full System (Auto-detect)
```bash
ros2 launch bringup full_system.launch.py
```

### Simulation Mode
```bash
ros2 launch bringup full_system.launch.py simulation:=true
```

### Real Hardware
```bash
ros2 launch bringup full_system.launch.py simulation:=false num_robots:=3
```

### Multi-Robot with Namespaces
```bash
ros2 launch bringup full_system.launch.py num_robots:=2
```

## Dependency Coordination
| Member | Component | Topic/Service Dependency |
|--------|-----------|--------------------------|
| Member 1 | Interfaces | Used by all |
| Member 2 | Simulation | Gazebo world & models |
| Member 3 | SLAM | Subscribes to /scan, publishes /map |
| Member 4 | Navigation | Subscribes to /map, publishes /cmd_vel |
| Member 5 | Sensors | Publishes /scan, /imu/data, etc. |

## Build Command
```bash
colcon build --packages-select bringup
```

## Success Criteria
✓ `ros2 launch bringup full_system.launch.py` starts entire system
✓ All nodes appear in `ros2 node list`
✓ ROS graph is connected: sensors → SLAM → Nav2 → controllers
✓ RViz displays all data correctly
✓ Multi-robot operation works without conflicts
✓ System recovers from individual component failures
✓ Parameter reconfiguration works
