from glob import glob
from setuptools import find_packages, setup

package_name = 'testing_tools'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/testing_tools/launch', glob('launch/*.launch.py')),
        ('share/testing_tools/config', glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Fire-Scout Team',
    maintainer_email='your.email@domain.com',
    description='Testing tools package for Fire-Scout.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'dummy_scan_pub = testing_tools.dummy_scan_pub:main',
            'dummy_odom_pub = testing_tools.dummy_odom_pub:main',
            'dummy_heartbeat_pub = testing_tools.dummy_heartbeat_pub:main',
            'dummy_fault_injector = testing_tools.dummy_fault_injector:main',
            'dummy_frontier_pub = testing_tools.dummy_frontier_pub:main',
            'dummy_camera_pub = testing_tools.dummy_camera_pub:main',
            'dummy_esp32_sensor_pub = testing_tools.dummy_esp32_sensor_pub:main',
            'namespace_lint_node = testing_tools.namespace_lint_node:main',
            'mock_camera_inference_node = testing_tools.mock_camera_inference_node:main',
        ]
    },
)
