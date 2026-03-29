# Fire-Scout ROS 2 Kilted Workspace

A multi-robot autonomous surveillance and mapping system built on ROS 2 Kilted, Gazebo Ionic, and TurtleBot3.

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

Before building, install the required ROS 2 Kilted packages:

```bash
sudo apt install ros-kilted-slam-toolbox
sudo apt install ros-kilted-nav2-core
sudo apt install ros-kilted-rviz2
sudo apt install ros-kilted-ros-gz
sudo apt install ros-kilted-ros-gz-sim
sudo apt install ros-kilted-turtlebot3
sudo apt install ros-kilted-turtlebot3-description
```

Set TurtleBot3 model (example: Burger):

```bash
echo 'export TURTLEBOT3_MODEL=burger' >> ~/.bashrc
source ~/.bashrc
```

**For multirobot map merging:** Try apt first, then build from source only if not available in your enabled repositories:

```bash
sudo apt install ros-kilted-multirobot-map-merge
```

Fallback (source build):

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

Launch only Gazebo Ionic simulation:

```bash
ros2 launch simulation gazebo_ionic.launch.py
```

## Notes

- **firescout_interfaces**: Provides custom messages for sensor data and trajectory references
- **simulation**: Targets Gazebo Ionic (`ros_gz_sim`) and TurtleBot3 models
- **bringup**: Python package with properly configured `setup.py` for launch file discovery

All custom interfaces are defined in `firescout_interfaces` and referenced by other packages via `<depend>firescout_interfaces</depend>`.
