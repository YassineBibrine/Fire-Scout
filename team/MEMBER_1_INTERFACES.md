# Member 1: Interfaces & Message Definitions

## Responsibility
Define and maintain all custom ROS 2 message types and services used across Fire-Scout.

## Primary Files
- `src/firescout_interfaces/msg/SensorData.msg`
- `src/firescout_interfaces/msg/ReferenceTrajectory.msg`
- `src/firescout_interfaces/srv/StartMapping.srv`
- `src/firescout_interfaces/srv/StopMapping.srv`
- `src/firescout_interfaces/CMakeLists.txt`
- `src/firescout_interfaces/package.xml`

## Tasks

### Phase 1: Interface Definition
- [ ] Refine `SensorData.msg` with all required sensor fields (IMU, LiDAR, camera, temperature, etc.)
- [ ] Refine `ReferenceTrajectory.msg` with trajectory planning fields
- [ ] Define `StartMapping.srv` with mapping configuration parameters
- [ ] Define `StopMapping.srv` with save/cleanup options
- [ ] Add any additional message types needed (RobotStatus, MapMetadata, etc.)

### Phase 2: Documentation
- [ ] Document all message fields and their units
- [ ] Create examples showing message usage
- [ ] Ensure backward compatibility notes

### Phase 3: Testing
- [ ] Test message generation with `colcon build`
- [ ] Verify messages are accessible from other packages

### Phase 4: Integration Governance
- [ ] Publish an interface contract table (topics, services, publishers, subscribers)
- [ ] Define message/service versioning and deprecation policy
- [ ] Add interface CI checks (message generation and import smoke test)
- [ ] Run compatibility review with Members 3, 4, and 5 before integration freeze

## Key Notes
- This package **must build first** — all other packages depend on it
- Ensure `<depend>firescout_interfaces</depend>` is declared in dependent packages' `package.xml`
- Any changes here require rebuilding dependent packages

## Build Command
```bash
cd ~/ws/Fire-Scout
colcon build --packages-select firescout_interfaces
```

## Success Criteria
✓ All interfaces compile without errors
✓ Message types are accessible to other packages
✓ Documentation is complete and clear
✓ Interface contract and versioning policy are adopted by all teams
