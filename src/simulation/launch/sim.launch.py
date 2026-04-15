from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():

    pkg_sim = get_package_share_directory('simulation')

    world = os.path.join(pkg_sim, 'worlds', 'world_1.sdf')

    # 🔥 IMPORTANT : dire à Gazebo où trouver les resources
    set_gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=pkg_sim
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py'
            )
        ),
        launch_arguments={'gz_args': world}.items()
    )

    return LaunchDescription([
        set_gz_resource_path,
        gazebo
    ])