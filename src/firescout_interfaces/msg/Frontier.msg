# Frontier cell representation
geometry_msgs/Pose centroid   # Center of frontier region
float32 size                  # Number of cells in frontier
float32 cost                  # Estimated exploration cost
float32 gain                  # Expected information gain
float32[] boundary_x          # X coordinates of boundary points
float32[] boundary_y          # Y coordinates of boundary points
