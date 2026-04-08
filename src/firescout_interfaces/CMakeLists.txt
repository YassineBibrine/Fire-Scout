cmake_minimum_required(VERSION 3.8)
project(firescout_interfaces)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(action_msgs REQUIRED)

# Messages
set(msg_files
  "msg/AuctionAnnouncement.msg"
  "msg/AuctionBid.msg"
  "msg/AuctionResult.msg"
  "msg/FaultEvent.msg"
  "msg/FireDetection.msg"
  "msg/Frontier.msg"
  "msg/FrontierArray.msg"
  "msg/HumanDetection.msg"
  "msg/Incident.msg"
  "msg/MapMergeStatus.msg"
  "msg/MissionState.msg"
  "msg/NodeStatus.msg"
  "msg/ReferenceTrajectory.msg"
  "msg/RobotHealth.msg"
  "msg/SensorData.msg"
  "msg/TaskAssignment.msg"
)

# Services
set(srv_files
  "srv/AckTask.srv"
  "srv/AssignTask.srv"
  "srv/GetRobotState.srv"
  "srv/ReportFault.srv"
  "srv/RequestAssistance.srv"
  "srv/ResolveIncident.srv"
  "srv/SetMapMergeEnabled.srv"
  "srv/SetRobotMode.srv"
  "srv/StartMapping.srv"
  "srv/StopMapping.srv"
)

# Actions
set(action_files
  "action/RescueHuman.action"
  "action/SuppressFire.action"
)

# Génération des interfaces
rosidl_generate_interfaces(${PROJECT_NAME}
  ${msg_files}
  ${srv_files}
  ${action_files}
  DEPENDENCIES
    std_msgs
    geometry_msgs
    nav_msgs
    sensor_msgs
    builtin_interfaces
    action_msgs
)

# Tests
if(BUILD_TESTING)
  find_package(ament_lint_common REQUIRED)
  find_package(ament_cmake_pytest REQUIRED)
  
  ament_add_pytest_test(test_msg_generation test/test_msg_generation.py)
  ament_add_pytest_test(test_srv_generation test/test_srv_generation.py)
  ament_add_pytest_test(test_action_generation test/test_action_generation.py)
endif()

# Installation
ament_export_dependencies(rosidl_default_runtime)

ament_package()

