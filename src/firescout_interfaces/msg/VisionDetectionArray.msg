# Array of vision detections published by camera_inference_node
# Phase 2 hybrid pipeline — QoS: BEST_EFFORT, sensor_data profile
string robot_id              # Robot namespace e.g. robot1
string camera_id             # Camera hardware ID
Detection[] detections       # All objects detected in this frame
builtin_interfaces/Time timestamp
