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
             'config/prioritization.yaml',
             'config/sensor_gateway.yaml',
             'config/camera_inference.yaml',
             'config/fusion_decision.yaml']),
    ],

    install_requires=['setuptools'],
    zip_safe=True,

    maintainer='Fire-Scout Team',
    maintainer_email='test@test.com',

    description='Response package',

    license='Apache-2.0',
    tests_require=['pytest'],

    entry_points={
        'console_scripts': [
            # Phase 1 nodes (modified for Phase 2 hybrid pipeline)
            'fire_detection_node = response.fire_detection_node:main',
            'human_detection_node = response.human_detection_node:main',
            'suppression_planning_node = response.suppression_planning_node:main',
            'rescue_planning_node = response.rescue_planning_node:main',
            # Phase 2 hybrid nodes
            'sensor_gateway_node = response.sensor_gateway_node:main',
            'camera_inference_node = response.camera_inference_node:main',
            'fusion_decision_node = response.fusion_decision_node:main',
            'coordination_bridge_node = response.coordination_bridge_node:main',
        ],
    },
)
