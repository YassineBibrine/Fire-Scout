# Array of vision detections published by camera_inference_node
# Phase 2 hybrid pipeline — QoS: BEST_EFFORT, depth=1 (not sensor_data default of 5)
# # depth=1 intentional: stale camera frames are worthless; subscribers must handle drops
string robot_id              # Robot namespace e.g. robot1
string camera_id             # Camera hardware ID
Detection[] detections       # All objects detected in this frame
builtin_interfaces/Time timestamp
