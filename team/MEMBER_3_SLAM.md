# Member 3: SLAM & Mapping

## Responsibility
Implement and configure SLAM (Simultaneous Localization and Mapping) using `slam_toolbox` and handle multi-robot map coordination.

## Primary Files
- `src/slam_node/` (new package - create this)
  - `src/slam_node/config/*.lua` (slam_toolbox configuration)
  - `src/slam_node/launch/online_async.launch.py`
  - `src/slam_node/package.xml`

## Dependencies
- `slam_toolbox` (installed via: `sudo apt install ros-jazzy-slam-toolbox`)
- `multirobot_map_merge` (build from source)

## Tasks

### Phase 1: Single-Robot SLAM
- [ ] Create `slam_node` package
- [ ] Create SLAM configuration file for online async mapping
- [ ] Create launch file: `online_async.launch.py`
  - Remap LiDAR scan topic
  - Configure map frame name
  - Set initial pose (if needed)
- [ ] Test SLAM with simulated robot

### Phase 2: Multi-Robot Map Merging
- [ ] Install/build `multirobot_map_merge` from source:
  ```bash
  cd ~/ros2_ws/src
  git clone https://github.com/cra-ros-pkg/multirobot_map_merge.git
  cd ~/ros2_ws && colcon build --packages-select multirobot_map_merge
  ```
- [ ] Create multi-robot SLAM launch file
- [ ] Configure map merging parameters
- [ ] Set up namespace handling for multiple robots

### Phase 3: Configuration & Tuning
- [ ] Tune SLAM parameters for Fire-Scout environment:
  - Loop closure thresholds
  - Feature detection settings
  - Map update rates
- [ ] Create configuration files for different scenarios (indoor, outdoor, etc.)

### Phase 4: Integration & Testing
- [ ] Test with simulation (Member 2)
- [ ] Generate merged maps from multi-robot scenarios
- [ ] Verify map persistence and recovery

## Package Structure
```
slam_node/
├── config/
│   ├── default_online_async.lua
│   └── firescout_mapper.lua
├── launch/
│   ├── online_async.launch.py
│   └── multi_robot_slam.launch.py
├── src/
├── CMakeLists.txt
└── package.xml
```

## Key Notes
- `slam_toolbox` is available via apt for Jazzy
- `multirobot_map_merge` must be built from source
- Coordinate with Member 5 (sensors) for LiDAR scan topics
- Coordinate with Member 6 (bringup) for integration into full system launch

## Build Commands
```bash
colcon build --packages-select slam_node
```

## Success Criteria
✓ Single robot generates valid occupancy maps
✓ Multiple robots' maps merge correctly
✓ Loop closures detected and corrected
✓ Maps persist across sessions
