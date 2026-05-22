# Fused decision from fusion_decision_node combining sensor + vision data
# Requires 2-of-2 temporal confirmation within 3 seconds to set *_confirmed = true
# Phase 2 hybrid pipeline — QoS: RELIABLE, KEEP_LAST depth 5
string robot_id              # Robot namespace e.g. robot1
bool fire_confirmed          # True when sensor + vision both confirm fire within 3 s
bool human_confirmed         # True when sensor + vision both confirm human within 3 s
float32 risk_level           # Combined risk score [0.0 - 1.0]
string recommended_action    # SUPPRESS | RESCUE | MONITOR | NONE
string[] contributing_sources  # IDs of sensor/camera sources that voted
float32 sensor_confidence    # Confidence from physical sensors [0.0 - 1.0]
float32 vision_confidence    # Confidence from camera inference [0.0 - 1.0]
builtin_interfaces/Time timestamp
