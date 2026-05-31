from glob import glob
from setuptools import find_packages, setup

package_name = 'monitoring'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/monitoring/launch', glob('launch/*.launch.py')),
        ('share/monitoring/config', glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Fire-Scout Team',
    maintainer_email='your.email@domain.com',
    description='Monitoring package for Fire-Scout.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={'console_scripts': [
        'topic_rate_monitor = monitoring.topic_rate_monitor_node:main',
        'latency_monitor    = monitoring.latency_monitor_node:main',
        'metrics_exporter   = monitoring.metrics_exporter_node:main',
    ]},
)
