# Fire-Scout ROS 2 Kilted Workspace

A multi-robot autonomous surveillance and mapping system built on ROS 2 Kilted, Gazebo Ionic, and TurtleBot3.

## Workspace Structure

```
src/
├── firescout_interfaces/     # Custom message/service/action contract
├── common_utils/             # Shared helper utilities (no runtime nodes)
├── simulation/               # Gazebo Ionic worlds/models/bridges
├── mapping/                  # SLAM + map merge
├── exploration/              # Frontier and auction coordination
├── response/                 # Fire/human detection and response
├── coordination/             # Mission and fault orchestration
├── monitoring/               # Latency/rate/metrics monitoring
├── testing_tools/            # Dummy publishers and integration helpers
└── bringup/                  # Full system launch composition
```

## Build Order

1. **firescout_interfaces** - Must build first (all runtime packages depend on it)
2. **Runtime packages** - simulation, mapping, exploration, response, coordination, monitoring, testing_tools
3. **bringup** - depends on runtime packages and composes full-system launch

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
- **monitoring**: Tracks topic rates and latency thresholds
- **testing_tools**: Provides dummy nodes for parallel team development and integration testing
- **bringup**: Composes global and per-robot launch stacks

All custom interfaces are defined in `firescout_interfaces` and referenced by other packages via `<depend>firescout_interfaces</depend>`.
