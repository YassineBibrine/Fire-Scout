# Robot health status message
string robot_name          # Robot namespace/name
float32 battery_percentage # Battery level 0-100
float32 cpu_load           # CPU load percentage
float32 memory_usage       # Memory usage percentage
float32 temperature        # CPU temperature in Celsius
bool is_connected          # Network connectivity status
builtin_interfaces/Time timestamp
