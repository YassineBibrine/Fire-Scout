from setuptools import find_packages, setup
from glob import glob

package_name = 'bringup'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/bringup/launch', glob('launch/*.launch.py')),
        ('share/bringup/config', glob('config/*.yaml')),
        ('share/bringup/config', glob('config/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Fire-Scout Team',
    maintainer_email='your.email@domain.com',
    description='Launch and configuration files for Fire-Scout',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
        ],
    },
)
