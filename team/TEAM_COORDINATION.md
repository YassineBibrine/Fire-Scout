# Fire-Scout Team Coordination Guide

## Team Members & Responsibilities

| # | Member | Role | Primary Package |
|---|--------|------|-----------------|
| 1 | **Interfaces** | Message/Service definitions | `firescout_interfaces` |
| 2 | **Simulation** | Gazebo Ionic + TurtleBot3 environment | `simulation` |
| 3 | **SLAM** | Mapping & localization | `slam_node` (new) |
| 4 | **Navigation** | Path planning & autonomy | `navigation_node` (new) |
| 5 | **Sensors** | Drivers & data processing | `sensor_drivers` (new) |
| 6 | **Bringup** | System integration & launch | `bringup` |

## Build Dependencies

```
firescout_interfaces (Member 1)
    ↓
    ├→ simulation (Member 2)
    ├→ slam_node (Member 3)
    ├→ sensor_drivers (Member 5)
    ├→ navigation_node (Member 4)
    └→ bringup (Member 6)
```

**Critical:** `firescout_interfaces` must build first. All other packages declare `<depend>firescout_interfaces</depend>`.

## Development Phases

### Phase 1: Foundation (Week 1)
- [ ] **Member 1** - Define all message types & services
- [ ] **Member 2** - Create Gazebo Ionic world and TurtleBot3 baseline setup
- [ ] **Member 6** - Create basic launch structure

**Sync Point:** All interfaces approved, simulation runs

### Phase 2: Perception (Week 2)
- [ ] **Member 5** - Create sensor drivers and data publishing
- [ ] **Member 3** - Implement SLAM with sensor data
- [ ] **Member 2** - Verify sensors work in simulation

**Sync Point:** SLAM generates maps, sensor data flows correctly

### Phase 3: Autonomy (Week 3)
- [ ] **Member 4** - Implement navigation stack
- [ ] **Member 3** - Tune SLAM for multi-robot scenarios
- [ ] **Member 2** - Add obstacles and complex environments

**Sync Point:** Robot navigates autonomously in simulation

### Phase 4: Integration (Week 4)
- [ ] **Member 6** - Integrate all components into single launch
- [ ] **All Members** - Test full system together
- [ ] **Member 6** - Create comprehensive documentation

**Sync Point:** Full system launch works end-to-end

### Phase 5: Multi-Robot (Week 5)
- [ ] **Member 3** - Implement map merging
- [ ] **Member 4** - Multi-robot navigation without collisions
- [ ] **Member 6** - Multi-robot launch configuration

**Sync Point:** Multiple robots work together

### Phase 6: Polish & Documentation (Week 6)
- [ ] **All Members** - Parameter tuning & optimization
- [ ] **All Members** - Comprehensive documentation
- [ ] **All Members** - Integration testing with real hardware

## Communication Protocol

### Daily Standups
Each member reports:
- ✓ What was completed yesterday
- ⚠ Current blockers
- → What's planned for today

### Code Integration Points

When Member X needs to integrate with Member Y:
1. Define interface in `firescout_interfaces` (Member 1)
2. Create topic/service names document
3. Add integration test to verify connection
4. Document expected data formats and rates

### Common Integration Points

| From | To | Message/Service | Rate |
|------|----|----|------|
| Member 5 | Member 3 | `sensor_msgs/LaserScan` → `/scan` | 10 Hz |
| Member 3 | Member 4 | `nav_msgs/OccupancyGrid` → `/map` | 1 Hz |
| Member 4 | Actuators | `geometry_msgs/Twist` → `/cmd_vel` | 20 Hz |
| Member 5 | Member 4 | `sensor_msgs/Imu` → `/imu/data` | 100 Hz |

## Testing Strategy

### Unit Testing (Individual)
- Each member tests their package independently
- Verify all nodes launch without errors
- Check output data types and rates

### Integration Testing (Pair)
- Member 5 + Member 3: Verify SLAM receives sensor data
- Member 3 + Member 4: Verify Nav2 receives maps
- Member 4 + Member 5: Verify IMU data is used

### System Testing (All)
- Member 6 launches full system
- Verify all data flows work end-to-end
- Monitor for errors and performance issues

### Multi-Robot Testing
- Test with 2, 3, and N robots
- Verify no namespace conflicts
- Check multi-robot SLAM map merging

## Build & Test Commands

### Individual Package Testing
```bash
# Member 1
colcon build --packages-select firescout_interfaces

# Member 2
colcon build --packages-select simulation

# Member 3
colcon build --packages-select slam_node

# Member 4
colcon build --packages-select navigation_node

# Member 5
colcon build --packages-select sensor_drivers

# Member 6
colcon build --packages-select bringup
```

### Full System Build
```bash
cd ~/Fire-Scout
colcon build
source install/setup.bash
```

### Launch Full System
```bash
# Simulation
ros2 launch bringup full_system.launch.py simulation:=true

# Real hardware
ros2 launch bringup full_system.launch.py simulation:=false
```

## Documentation Requirements

Each member must provide:
1. **README** in their package directory
2. **Launch file comments** explaining parameters
3. **Configuration file documentation** (YAML comments)
4. **API documentation** for custom nodes/libraries
5. **Troubleshooting guide** for common issues

## Repository Guidelines

### Branch Strategy
```
main (stable, tested)
  ├── feature/member1-interfaces
  ├── feature/member2-simulation
  ├── feature/member3-slam
  ├── feature/member4-navigation
  ├── feature/member5-sensors
  └── feature/member6-bringup
```

### Commit Convention
```
[MEMBER-#] Brief description

Longer description if needed.

Relates to: #issue_number
```

Example:
```
[MEMBER-3] Implement online async SLAM

- Configured slam_toolbox for Fire-Scout
- Added multi-robot map merging
- Tuned loop closure thresholds

Relates to: #15
```

### PR Review Checklist
- [ ] Code compiles without warnings
- [ ] All dependencies listed in package.xml
- [ ] Launch files tested independently
- [ ] ROS naming conventions followed
- [ ] Comments explain non-obvious logic
- [ ] Tests pass locally

## Blockers & Dependencies

### Potential Blockers
1. **Member 1 → All**: If interfaces aren't defined, no one else can start
   - **Mitigation**: Define basic interfaces early, add more later
   
2. **Member 2 → Member 5**: Simulation sensors need Gazebo plugins
   - **Mitigation**: Member 2 and 5 coordinate on plugin selection
   
3. **Member 5 → Members 3, 4**: Without sensor drivers, SLAM and Nav2 have no input
   - **Mitigation**: Create mock sensor publishers for early testing
   
4. **Member 3 → Member 4**: Navigation needs good maps from SLAM
   - **Mitigation**: Use pre-recorded maps for early Nav2 development

## Success Metrics

- ✓ All packages compile without errors
- ✓ With `ros2 launch bringup full_system.launch.py` system is fully operational
- ✓ Single robot autonomously navigates in simulation
- ✓ Multiple robots coordinate without collisions
- ✓ All code documented and tested
- ✓ System runs for 1+ hour without crashing
- ✓ Performance meets requirements (1Hz maps, 10Hz control)

## Contact & Escalation

If you're blocked:
1. Check if another member can unblock you
2. If blocking another member, prioritize their work
3. Escalate to project lead if interdependency is complex
4. Consider creating stub/mock implementations for testing
