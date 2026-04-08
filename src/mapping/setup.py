from glob import glob
from setuptools import find_packages, setup

package_name = 'mapping'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/mapping/launch', glob('launch/*.launch.py')),
        ('share/mapping/config', glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Fire-Scout Team',
    maintainer_email='your.email@domain.com',
    description='Mapping package skeleton for Fire-Scout.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={'console_scripts': [
        'slam_wrapper_node = mapping.slam_wrapper_node:main',
        'map_merge_node    = mapping.map_merge_node:main',
    ]},
)
