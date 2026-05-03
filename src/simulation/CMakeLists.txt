cmake_minimum_required(VERSION 3.8)
project(simulation)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(firescout_interfaces REQUIRED)

# Install all asset directories (config was missing before)
install(DIRECTORY worlds models launch config
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_common REQUIRED)
  find_package(ament_cmake_pytest REQUIRED)

  ament_add_pytest_test(test_spawn_namespaces test/test_spawn_namespaces.py)
  ament_add_pytest_test(test_bridge_topics    test/test_bridge_topics.py)
  ament_add_pytest_test(test_clock_available  test/test_clock_available.py)
endif()

ament_package()