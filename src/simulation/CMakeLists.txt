cmake_minimum_required(VERSION 3.8)
project(simulation)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(firescout_interfaces REQUIRED)

install(DIRECTORY worlds models launch
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  scripts/fire_suppression_sim_node.py
  scripts/proximity_fire_removal.py
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_bridge_topics test/test_bridge_topics.py)
  ament_add_pytest_test(test_clock_available test/test_clock_available.py)
  ament_add_pytest_test(test_lidar_sensor_model test/test_lidar_sensor_model.py)
  ament_add_pytest_test(test_spawn_robot_launch test/test_spawn_robot_launch.py)
  ament_add_pytest_test(test_spawn_namespaces test/test_spawn_namespaces.py)
  # Phase 2 tests
  ament_add_pytest_test(test_camera_bridge_topic test/test_camera_bridge_topic.py)
  ament_add_pytest_test(test_fire_entity_spawn test/test_fire_entity_spawn.py)
endif()

ament_package()
