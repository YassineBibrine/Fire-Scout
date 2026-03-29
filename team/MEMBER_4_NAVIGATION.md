# Member 4: Navigation & Path Planning

## Responsibility
Implement autonomous navigation using Nav2 stack, including path planning, obstacle avoidance, and behavior trees.

## Primary Files
- `src/navigation_node/` (new package - create this)
  - `src/navigation_node/config/nav2_params.yaml`
  - `src/navigation_node/launch/nav2_launch.py`
  - `src/navigation_node/behavior_trees/` (BT XML files)
  - `src/navigation_node/package.xml`

## Dependencies
- `nav2_core` (installed via: `sudo apt install ros-kilted-nav2-core`)
- `nav2_bringup`
- `nav2_behaviors`

## Tasks

### Phase 1: Nav2 Stack Setup
- [ ] Create `navigation_node` package
- [ ] Create Nav2 parameters YAML file with:
  - Costmap configuration
  - Planner settings (Dijkstra, DWB, etc.)
  - Controller parameters
  - Recovery behaviors
- [ ] Create launch file: `nav2_launch.py`

### Phase 2: Path Planning
- [ ] Configure global planner:
  - A* or Dijkstra algorithm selection
  - Map resolution and inflation radius
- [ ] Configure local controller:
  - DWB local controller or TEB
  - Velocity and acceleration limits
  - Safety margins

### Phase 3: Costmap & Collision Avoidance
- [ ] Setup global costmap (static map from SLAM)
- [ ] Setup local costmap (local obstacle detection from sensors)
- [ ] Configure obstacle inflation and cost propagation
- [ ] Define no-go zones and safety boundaries

### Phase 4: Behavior & Recovery
- [ ] Define behavior tree for autonomous missions:
  - Navigate to goal
  - Handle stuck situations
  - Retry logic
- [ ] Implement recovery behaviors:
  - Spin recovery
  - Back-up recovery
  - Clear costmap action

### Phase 5: Testing & Integration
- [ ] Test navigation in simulation
- [ ] Test multi-robot navigation without collisions
- [ ] Verify goal cancellation and recovery
- [ ] Integrate with mission planning system

## Package Structure
```
navigation_node/
├── config/
│   ├── nav2_params.yaml
│   └── maps/
├── launch/
│   └── nav2_launch.py
├── behavior_trees/
│   └── navigate.xml
├── src/
├── CMakeLists.txt
└── package.xml
```

## Key Notes
- Relies on maps from Member 3 (SLAM)
- Uses sensor data from Member 5 (sensors)
- Coordinate with Member 2 (simulation) for environment testing
- Integrate into Member 6's system launch

## Build Command
```bash
colcon build --packages-select navigation_node
```

## Success Criteria
✓ Robot navigates to goal without manual intervention
✓ Obstacles are avoided autonomously
✓ Recovery behaviors work when stuck
✓ Multiple robots don't collide
✓ Performance: 1Hz navigation updates minimum
