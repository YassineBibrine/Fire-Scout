# Raw fire sensor alert published by sensor_gateway_node from /robotX/esp32/sensors
# Phase 2 hybrid pipeline — QoS: RELIABLE, KEEP_LAST depth 5
string robot_id              # Robot namespace e.g. robot1
bool flame_detected          # IR flame sensor triggered
float32 smoke_level          # Smoke density [0.0 - 1.0]
float32 gas_level            # Gas/CO concentration [0.0 - 1.0]
float32 temperature          # Ambient temperature in Celsius
float32 normalized_risk      # Fused sensor risk score [0.0 - 1.0]
string source_id             # Physical sensor hardware ID
builtin_interfaces/Time timestamp
