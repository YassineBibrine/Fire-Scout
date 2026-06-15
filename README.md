<p align="center">
  <img src="fire-scout-logo.png" alt="Fire-Scout Logo" width="200"/>
</p>

<h1 align="center">Fire-Scout</h1>
<p align="center">
  <strong>Multi-Robot Autonomous Surveillance & Fire Detection System</strong><br/>
  ROS 2 Kilted · Gazebo Ionic · TurtleBot3
</p>

---

## Overview

Fire-Scout is a multi-robot autonomous surveillance and fire detection system. A fleet of three TurtleBot3 Burger robots collaboratively explores an unknown indoor environment, builds a shared 2-D map using SLAM, detects fire hazards through a hybrid sensor-and-vision pipeline, and coordinates a suppression response all within a single ROS 2 Kilted workspace.

---

## Workspace Structure

```
src/
├── firescout_interfaces/     # Custom message/service/action contracts (build first)
├── common_utils/             # Shared geometry, math, QoS, and namespace helpers (no runtime nodes)
├── simulation/               # Gazebo Ionic worlds, robot spawn, ros_gz bridges, fire suppression node
├── mapping/                  # Per-robot SLAM (slam_toolbox) + global map merge
├── exploration/              # Frontier detection + auction-based global task allocator
├── response/                 # Hybrid sensor+vision fire detection, incident reporting
├── coordination/             # Mission manager, task assignment service, cmd_vel safety filter
├── monitoring/               # Topic rate and latency watchdog, metrics alerts
├── testing_tools/            # Dummy publishers and integration helpers for parallel development
└── bringup/                  # Full-system and per-robot launch composition, RViz config
```

---

## Build Order

1. **`firescout_interfaces`** : must build first; all runtime packages depend on its generated message types.
2. **Runtime packages** : `simulation`, `mapping`, `exploration`, `response`, `coordination`, `monitoring`, `testing_tools` (order within this group is resolved automatically).
3. **`bringup`** : depends on all runtime packages and composes the full-system launch.

`colcon build` resolves this order automatically via `package.xml` dependencies.

---

## Installation Requirements

### ROS 2 Kilted packages

```bash
sudo apt install ros-kilted-slam-toolbox
sudo apt install ros-kilted-rviz2
sudo apt install ros-kilted-ros-gz
sudo apt install ros-kilted-ros-gz-sim
sudo apt install ros-kilted-turtlebot3
sudo apt install ros-kilted-turtlebot3-description
```

### TurtleBot3 model

```bash
echo 'export TURTLEBOT3_MODEL=burger' >> ~/.bashrc
source ~/.bashrc
```

### Multi-robot map merging

Try `apt` first; build from source only if the package is not available in your enabled repositories:

```bash
sudo apt install ros-kilted-multirobot-map-merge
```

<details>
<summary>Fallback : build from source</summary>

```bash
cd ~/ros2_ws/src
git clone https://github.com/cra-ros-pkg/multirobot_map_merge.git
cd ~/ros2_ws
colcon build --packages-select multirobot_map_merge
```
</details>

### Nav2 (optional)

Nav2 is **disabled by default** (`enable_nav2:=false`). The files `nav2_robot.launch.py` and `nav2_params.yaml` are retained for optional experiments. To use Nav2, install the stack:

```bash
sudo apt install ros-kilted-nav2-bringup
```

---

## Building

```bash
cd /path/to/Fire-Scout
colcon build \
    --cmake-args \
        -DPython3_EXECUTABLE=/usr/bin/python3 \
        -DPYTHON_EXECUTABLE=/usr/bin/python3
source install/setup.bash
```

---

## Running

### Full system (recommended)

Use the provided launch script. It sets the correct DDS environment, cleans stale state, builds, and launches:

```bash
./launch_sim.sh
```

This is equivalent to:

```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI="file://$(pwd)/config/cyclonedds.xml"
ros2 launch bringup full_system.launch.py \
    simulation:=true \
    use_sim_time:=true \
    world_name:=villa_world \
    enable_nav2:=false \
    enable_fire_suppression:=true \
    launch_profile:=sim
```

### Launch only the Gazebo simulation

```bash
ros2 launch simulation sim.launch.py world_name:=villa_world
```

### Manual task assignment

Send a navigation task to a specific robot at runtime:

```bash
python assign_task.py robot1 2.0 2.0
# Usage: python assign_task.py <robot_id> <x> <y>
```

---

## Launch Arguments

All arguments for `bringup/full_system.launch.py`:

| Argument | Default | Description |
|---|---|---|
| `simulation` | `true` | Launch Gazebo and bridge nodes when `true` |
| `use_sim_time` | `true` | Use the `/clock` topic from Gazebo |
| `world_name` | `villa_world` | Gazebo SDF world name |
| `start_paused` | `false` | Start Gazebo paused (`false` = live sensor streams) |
| `launch_profile` | `sim` | Response pipeline profile: `sim`, `robot`, or `debug` |
| `model_path` | _(empty)_ | Path to YOLO model file — required when `launch_profile:=robot` |
| `enable_nav2` | `false` | Launch Nav2 stack for each robot |
| `enable_fire_suppression` | `true` | Remove Gazebo fire entities on confirmed suppression |
| `include_response` | `true` | Include the hybrid fire-detection pipeline |
| `rviz_config` | bringup default | Source RViz config (copied to a runtime path on launch) |
| `rviz_config_out` | `/tmp/firescout_viz_runtime.rviz` | Runtime copy destination for RViz config |

---

## System Architecture

### Robot fleet

Three TurtleBot3 Burger robots are spawned at fixed positions at launch:

| Robot | Spawn X | Spawn Y | Launch delay |
|---|---|---|---|
| `robot1` | −2.0 m | −2.0 m | +15 s |
| `robot2` | 0.0 m | −2.0 m | +19 s |
| `robot3` | 2.0 m | −2.0 m | +23 s |

Robots are staggered to prevent DDS discovery collisions. RViz starts at +29 s to allow all TF trees to stabilise.

`robot1` is the designated auto-suppression robot: it is the only robot that automatically acts on a fire detection to execute suppression.

### TF frame tree

Each robot maintains an independent transform chain under its own namespace:

```
map
├── robot1/map  →  robot1/odom  →  robot1/base_link  →  robot1/lidar
│                                                    →  robot1/camera
├── robot2/map  →  robot2/odom  →  robot2/base_link  →  robot2/lidar
│                                                    →  robot2/camera
└── robot3/map  →  robot3/odom  →  robot3/base_link  →  robot3/lidar
                                                     →  robot3/camera
```

Static transforms (`map → robotN/map`, `base_link → sensor`) broadcast at 10 000 Hz (zero-buffer identity). SLAM-linked transforms update at ~10–13 Hz; odometry at ~12 Hz.

### Global stack (launched once)

| Component | Package | Purpose |
|---|---|---|
| Map merge | `mapping` | Stitches per-robot occupancy grids into `/map` |
| Auction coordinator | `exploration` | Assigns frontiers to robots via market-based bidding |
| Incident registry | `response` | Global store of confirmed fire incidents |
| Mission manager | `coordination` | Assigns response tasks based on robot proximity |
| Coordination bridge | `coordination` | Bridges coordination data across robot namespaces |
| Monitoring watchdog | `monitoring` | Tracks topic rates and latency; publishes `/monitoring/alerts` |
| Global simulation bridge | `simulation` | `gz → ROS 2` bridge for world-level topics |

### Per-robot stack (launched × 3)

| Component | Package | Purpose |
|---|---|---|
| Robot spawn | `simulation` | Inserts TurtleBot3 model into Gazebo |
| Robot bridge | `simulation` | `gz → ROS 2` bridge for per-robot sensor topics |
| SLAM | `mapping` | `slam_toolbox` online async mode on `robotN/scan` |
| Frontier explorer | `exploration` | Detects frontiers on local map, publishes bids |
| cmd_vel safety | `coordination` | Clamps velocity commands that would cause collisions |
| Hybrid pipeline | `response` | Sensor + vision confidence fusion, incident reporting |
| Nav2 _(optional)_ | `bringup` | DWB local planner + NavFn global planner, lifecycle-managed |

### Fire suppression node

`fire_suppression_sim_node.py` (starts at +8 s) monitors robot positions against Gazebo fire entity locations:

| Parameter | Value |
|---|---|
| `suppression_radius_m` | 2.5 m |
| `fire_match_radius_m` | 4.0 m |
| `auto_suppress_when_close_radius_m` | 5.0 m |
| `allow_any_robot_to_suppress` | `false` |
| `auto_suppress_on_detection_robot_ids` | `['robot1']` |
| `auto_suppress_on_detection_model_names` | `['fire_entity']` |

### Hybrid detection pipeline

The `response` package supports three launch profiles selected via `launch_profile`:

| Profile | Sensor channel | Vision channel |
|---|---|---|
| `sim` | Proximity to Gazebo fire entity models | Stub node with configurable confidence |
| `robot` | Real hardware heat threshold (camera feed) | YOLOv8 inference (requires `model_path`) |
| `debug` | Both sim and robot pipelines active in parallel | Both |

Confidence fusion (from `common_utils`):

```
combined = clamp((sensor_conf × 0.6 + vision_conf × 0.4), 0.0, 1.0)
```

A detection is confirmed when `combined ≥ 0.7` (configurable).

---

## Middleware and DDS Configuration

Fire-Scout uses **CycloneDDS** (`rmw_cyclonedds_cpp`) configured via `config/cyclonedds.xml`:

| Setting | Value | Reason |
|---|---|---|
| `MaxAutoParticipantIndex` | 200 | Accommodates many participants from 3 robots |
| `EnableMulticastLoopback` | `true` | Required for loopback communication in simulation |
| `MaxMessageSize` | 64 KB | Prevents large messages saturating the loopback interface |
| `WhcHigh` watermark | 500 KB | Buffers bursty transmissions without dropping messages |

QoS profiles (defined in `common_utils/qos_profiles.py`):

| Profile | Policy | Used for |
|---|---|---|
| `SENSOR_QOS` | `sensor_data` (best-effort) | High-rate LiDAR and camera streams |
| `STATUS_QOS` | `reliable` | Incident reports, status messages |
| `COMMAND_QOS` | `reliable` | Navigation commands, task assignments |

The `RMW_IMPLEMENTATION` and `CYCLONEDDS_URI` environment variables **must** be set before launching any ROS process. `launch_sim.sh` handles this automatically.

---

## Nav2 (Optional)

When `enable_nav2:=true`, each robot launches the following Nav2 nodes inside its namespace via `PushRosNamespace`:

- `controller_server` — DWB local planner (max 0.35 m/s, 1.25 rad/s)
- `planner_server` — NavFn global planner
- `behavior_server` — Spin, BackUp, Wait recovery behaviours
- `bt_navigator` — Behaviour Tree executor with 1 Hz replanning and automatic costmap clearing
- `lifecycle_manager` — Autostart, 30 s bond timeout

The Nav2 behaviour tree (`navigate_w_replanning_only_if_path_becomes_invalid.xml`) replans at 1 Hz and applies recovery actions in sequence (clear costmaps → spin → wait → back-up) with up to 6 retries.

> **Note:** Nav2 integration with the dynamic merged map is experimental. The `amcl`-based localiser expects a static global map; subtle shifts from `multirobot_map_merge` can cause costmap stale data and path rejection. Use with `enable_nav2:=true` for point-to-point navigation experiments only, not during active exploration.

---

## Testing

Run all tests (builds first, then tests, then prints results):

```bash
./run_tests_ros.sh
```

Run tests for a specific package only:

```bash
./run_tests_ros.sh bringup
```

The script clears any active virtual environments and conda prefixes to ensure the system Python and ROS tooling are used.

### Bringup test suite

| Test | What it checks |
|---|---|
| `test_full_launch_smoke` | `generate_launch_description()` returns a valid, non-empty `LaunchDescription` |
| `test_full_launch_hybrid_sim_profile` | All 3 robots receive a `hybrid_pipeline` include with the correct `launch_profile` argument |
| `test_robot_stack_launch_args` | `robot1`, `robot2`, `robot3` IDs are all passed through to robot stack includes |
| `test_rviz_config` | RViz fixed frame is `map` under `Global Options`; map displays subscribe to `/map`, `/robot1/map`, `/robot2/map`, `/robot3/map` |

---

## Key Files Reference

| File | Purpose |
|---|---|
| `launch_sim.sh` | One-shot build + launch with correct DDS environment |
| `run_tests_ros.sh` | Build + test runner (accepts optional package filter) |
| `assign_task.py` | CLI for manual task assignment via the coordination service |
| `config/cyclonedds.xml` | CycloneDDS tuning for multi-robot participant limits |
| `src/bringup/launch/full_system.launch.py` | Top-level system launch |
| `src/bringup/launch/global_stack.launch.py` | Global nodes (map merge, auction, incident registry, etc.) |
| `src/bringup/launch/robot_stack.launch.py` | Per-robot node group (spawn, SLAM, exploration, response) |
| `src/bringup/launch/nav2_robot.launch.py` | Optional Nav2 stack per robot |
| `src/bringup/config/nav2_params.yaml` | Nav2 DWB controller and costmap parameters (all 3 robots) |
| `src/bringup/config/namespace_map.yaml` | Declares the `['robot1', 'robot2', 'robot3']` fleet |
| `src/bringup/config/firescout_viz.rviz` | RViz layout: merged map + 3 individual robot maps |
| `src/common_utils/common_utils/math_utils.py` | `weighted_confidence()` and `clamp()` |
| `src/common_utils/common_utils/geometry_utils.py` | `distance_2d()` |
| `src/common_utils/common_utils/qos_profiles.py` | `SENSOR_QOS`, `STATUS_QOS`, `COMMAND_QOS` |
| `src/common_utils/common_utils/namespace_utils.py` | `namespaced(robot_id, topic)` helper |
| `src/common_utils/config/defaults.yaml` | `default_timeout_sec: 5.0` |

---

## Notes

- **`firescout_interfaces`** is the single source of truth for all inter-package message, service, and action types. All runtime packages declare `<depend>firescout_interfaces</depend>` in their `package.xml`.
- **`simulation`** targets Gazebo Ionic (`ros_gz_sim`) with TurtleBot3 Burger models. It provides separate launch files for spawning individual robots, per-robot bridges, global bridges, and the fire suppression node.
- **`mapping`** runs one `slam_toolbox` instance per robot in online asynchronous mode. Map merge succeeds once robots share ~15% overlapping coverage.
- **`exploration`** computes frontier utility as `information_gain − λ × distance` (λ = 1.0 default) and awards frontiers via a global auction.
- **`coordination`** provides the `/coordination/services/assign_task` service (callable via `assign_task.py`) and the `cmd_vel_safety_node` which wraps each robot's velocity channel.
- **`monitoring`** publishes rate and latency alerts to `/monitoring/alerts`. Useful for diagnosing SLAM stalls under CPU load.
- **`testing_tools`** provides dummy publisher nodes so team members can develop packages in isolation without a running Gazebo instance.
- **`bringup`** stages robot launches with 4-second offsets and delays RViz by 29 seconds to avoid DDS discovery collisions and TF lookup failures on startup.
