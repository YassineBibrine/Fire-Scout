from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():

    pkg_sim = get_package_share_directory('simulation')
    pkg_turtlebot3 = get_package_share_directory('turtlebot3_description')

    world = os.path.join(pkg_sim, 'worlds', 'world_1.sdf')

    # 🔥 IMPORTANT : Tell Gazebo where to find resources (meshes, models, etc)
    ros_share_dir = os.path.dirname(pkg_sim)  # Get /opt/ros/kilted/share/
    
    # Set GZ_SIM_RESOURCE_PATH for simulation resources
    gz_resource_path = f'{pkg_sim}{os.pathsep}{ros_share_dir}'
    set_gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=gz_resource_path
    )
    
    # Set GZ_MODEL_PATH for model/mesh resolution
    set_gz_model_path = SetEnvironmentVariable(
        name='GZ_MODEL_PATH',
        value=ros_share_dir
    )

    # Disable FastDDS shared memory transport for this launch to reduce port-lock spam.
    set_fastrtps_shm = SetEnvironmentVariable(
        name='FASTDDS_BUILTIN_TRANSPORTS',
        value='UDPv4'
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
        set_gz_model_path,
        set_fastrtps_shm,
        gazebo
    ])
