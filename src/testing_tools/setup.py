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
            'dummy_scan_pub = testing_tools.scan_pub_node:main',
            'dummy_odom_pub = testing_tools.odom_pub_node:main',
            'dummy_camera_pub = testing_tools.camera_pub_node:main',
            'dummy_heartbeat_pub = testing_tools.heartbeat_pub_node:main',
        ]
    },
)
