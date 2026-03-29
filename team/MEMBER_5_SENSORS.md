# Member 5: Sensor Integration & Drivers

## Responsibility
Implement sensor drivers and data processing for LiDAR, IMU, cameras, and other Fire-Scout sensors.

## Primary Files
- `src/sensor_drivers/` (new package - create this)
  - `src/sensor_drivers/src/` (driver code)
  - `src/sensor_drivers/launch/` (sensor launch files)
  - `src/sensor_drivers/config/` (sensor calibration parameters)
  - `src/sensor_drivers/package.xml`

## Sensor Types
- **LiDAR**: 2D/3D scan data (used by SLAM - Member 3)
- **IMU**: Acceleration, angular velocity, orientation
- **Camera**: RGB/thermal imaging (optional)
- **Temperature/Environmental**: Fire detection sensors

## Tasks

### Phase 1: LiDAR Integration
- [ ] Create LiDAR driver node for:
  - Simulation: Use Gazebo plugin data
  - Hardware: Integrate with actual LiDAR (Velodyne, Livox, etc.)
- [ ] Output as `sensor_msgs/LaserScan` or `sensor_msgs/PointCloud2`
- [ ] Create launch file: `lidar.launch.py`
- [ ] Configure frame name and tf publishing

### Phase 2: IMU Integration
- [ ] Create IMU driver node
- [ ] Output as `sensor_msgs/Imu`
- [ ] Implement calibration (bias, scale, rotation)
- [ ] Create launch file: `imu.launch.py`

### Phase 3: Camera Integration (Optional)
- [ ] Create camera driver for RGB/thermal
- [ ] Output as `sensor_msgs/Image` (ROS Image transport)
- [ ] Setup compressed image publishing for bandwidth
- [ ] Create launch file: `camera.launch.py`

### Phase 4: Fire Detection Sensors
- [ ] Create temperature/environmental sensor integration
- [ ] Publish using custom `firescout_interfaces/SensorData` message
- [ ] Implement data fusion for multi-sensor detection
- [ ] Create launch file: `fire_sensors.launch.py`

### Phase 5: Data Quality & Filtering
- [ ] Implement sensor data validation (NaN, outlier detection)
- [ ] Add noise filtering where appropriate
- [ ] Implement sensor failure detection
- [ ] Create diagnostic publisher for health monitoring

### Phase 6: Testing & Calibration
- [ ] Test each sensor independently
- [ ] Verify data rates and latency
- [ ] Create calibration procedures documentation
- [ ] Perform system integration tests with Member 3 (SLAM) and Member 4 (Navigation)

## Package Structure
```
sensor_drivers/
├── include/
├── src/
│   ├── lidar_driver_node.cpp
│   ├── imu_driver_node.cpp
│   ├── camera_driver_node.cpp
│   └── fire_sensor_node.cpp
├── config/
│   ├── lidar_params.yaml
│   ├── imu_params.yaml
│   └── camera_params.yaml
├── launch/
│   ├── lidar.launch.py
│   ├── imu.launch.py
│   ├── camera.launch.py
│   ├── fire_sensors.launch.py
│   └── all_sensors.launch.py
├── CMakeLists.txt
└── package.xml
```

## Dependencies
- Coordinate with Member 1 for `firescout_interfaces::SensorData`
- Use standard ROS message types: `sensor_msgs/LaserScan`, `sensor_msgs/Imu`, `sensor_msgs/Image`

## Build Command
```bash
colcon build --packages-select sensor_drivers
```

## Topic Mapping (ROS Graph)
```
sensor_drivers/
├── /scan (LiDAR) → Member 3 SLAM
├── /imu/data (IMU) → Member 4 Navigation
├── /camera/image_raw (Camera) → Applications
└── /fire_detection (Custom) → Fire detection system
```

## Success Criteria
✓ All sensors produce valid data in simulation
✓ Data rates meet requirements (see launch configs)
✓ No dropped frames or data loss
✓ Proper TF transforms published
✓ Sensor health monitoring working
✓ Calibration procedures documented
