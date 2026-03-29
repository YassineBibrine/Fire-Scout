cmake_minimum_required(VERSION 3.8)
project(firescout_interfaces)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(map_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)

set(msg_files
  "msg/SensorData.msg"
  "msg/ReferenceTrajectory.msg"
  "msg/RobotHealth.msg"
  "msg/FaultEvent.msg"
  "msg/MissionState.msg"
  "msg/NodeStatus.msg"
  "msg/Frontier.msg"
  "msg/FrontierArray.msg"
  "msg/AuctionAnnouncement.msg"
  "msg/AuctionBid.msg"
  "msg/AuctionResult.msg"
  "msg/TaskAssignment.msg"
  "msg/FireDetection.msg"
  "msg/HumanDetection.msg"
  "msg/Incident.msg"
  "msg/MapMergeStatus.msg"
)

set(srv_files
  "srv/StartMapping.srv"
  "srv/StopMapping.srv"
  "srv/SetRobotMode.srv"
  "srv/ReportFault.srv"
  "srv/AssignTask.srv"
  "srv/AckTask.srv"
  "srv/RequestAssistance.srv"
  "srv/ResolveIncident.srv"
  "srv/GetRobotState.srv"
  "srv/SetMapMergeEnabled.srv"
)

set(action_files
  "action/SuppressFire.action"
  "action/RescueHuman.action"
)

rosidl_generate_interfaces(${PROJECT_NAME}
  ${msg_files}
  ${srv_files}
  ${action_files}
  DEPENDENCIES std_msgs builtin_interfaces geometry_msgs nav_msgs map_msgs sensor_msgs
)

ament_package()
