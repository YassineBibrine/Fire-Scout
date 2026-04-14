from setuptools import setup

package_name = 'response'

setup(
    name=package_name,
    version='0.0.0',

    packages=[package_name],

    data_files=[
    ('share/ament_index/resource_index/packages',
        ['resource/' + package_name]),

    ('share/' + package_name,
        ['package.xml']),

    ('share/' + package_name + '/launch',
        ['launch/detection_robot.launch.py',
         'launch/incident_global.launch.py']),

    ('share/' + package_name + '/config',
        ['config/fire_detection.yaml',
         'config/human_detection.yaml',
         'config/prioritization.yaml']),
    ],

    install_requires=['setuptools'],
    zip_safe=True,

    maintainer='Fire-Scout Team',
    maintainer_email='test@test.com',

    description='Response package',

    license='Apache-2.0',

    entry_points={
        'console_scripts': [
            'fire_detection_node = response.fire_detection_node:main',
        ],
    },
)
