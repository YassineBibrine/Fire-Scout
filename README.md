# Fire-Scout ROS 2 Jazzy Workspace

A multi-robot autonomous surveillance and mapping system built on ROS 2 Jazzy.

## Workspace Structure

```
src/
├── firescout_interfaces/     # Custom message and service definitions (builds first)
│   └── msg/
├── simulation/               # Gazebo simulation environment
│   ├── worlds/
│   ├── models/
│   └── launch/
└── bringup/                  # Launch and configuration files
    └── launch/
```

## Build Order

1. **firescout_interfaces** - Must build first (other packages depend on it)
2. **simulation** - Depends on firescout_interfaces
3. **bringup** - Depends on firescout_interfaces

`colcon build` handles this automatically via `package.xml` dependencies.

## Building

```bash
cd /home/yassine/vs_code_projects/Fire-Scout
colcon build
. install/setup.bash
```

## Installation Requirements

Before building, install the required ROS 2 Jazzy packages:

```bash
sudo apt install ros-jazzy-slam-toolbox
sudo apt install ros-jazzy-nav2-core
sudo apt install ros-jazzy-rviz2
```

**For multirobot map merging:** Clone and build from source (not available via apt in Jazzy):

```bash
cd ~/ros2_ws/src
git clone https://github.com/cra-ros-pkg/multirobot_map_merge.git
cd ~/ros2_ws
colcon build --packages-select multirobot_map_merge
```

## Running

Launch the full system:

```bash
ros2 launch bringup full_system.launch.py
```

## Notes

- **firescout_interfaces**: Provides custom messages for sensor data and trajectory references
- **simulation**: Uses `ament_cmake` with proper asset installation (worlds, models) to `share/`
- **bringup**: Python package with properly configured `setup.py` for launch file discovery

All custom interfaces are defined in `firescout_interfaces` and referenced by other packages via `<depend>firescout_interfaces</depend>`.
