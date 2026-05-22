# Single vision detection produced by camera_inference_node
# Part of the Phase 2 hybrid sensor-fusion pipeline
string class_label           # Detected class: fire | human | smoke
float32 confidence           # Inference confidence [0.0 - 1.0]
float32[4] bounding_box      # Pixel coords: [x_min, y_min, x_max, y_max]
geometry_msgs/Pose estimated_pose  # Estimated 3D pose in robot frame
