from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    start_paused = LaunchConfiguration('start_paused')

    pkg_sim = get_package_share_directory('simulation')

    # Use the provided world file `world_1.sdf` from the simulation/worlds dir.
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
    # Include the simulation package and the ROS share dir so Gazebo can
    # resolve local `models/` and package-installed models.
    set_gz_model_path = SetEnvironmentVariable(
        name='GZ_MODEL_PATH',
        value=f'{pkg_sim}{os.pathsep}{ros_share_dir}'
    )

    # Disable FastDDS shared memory transport for this launch to reduce port-lock spam.
    set_fastrtps_shm = SetEnvironmentVariable(
        name='FASTDDS_BUILTIN_TRANSPORTS',
        value='UDPv4'
    )

    start_paused_arg = DeclareLaunchArgument(
        'start_paused',
        default_value='false',
        description='Open Gazebo paused so models and bridges settle before physics runs.',
    )

    def _gazebo_args(context):
        paused = start_paused.perform(context).lower() in ('true', '1', 'yes')
        run_flag = '' if paused else '-r '
        return [IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    get_package_share_directory('ros_gz_sim'),
                    'launch',
                    'gz_sim.launch.py'
                )
            ),
            launch_arguments={'gz_args': f"{run_flag}{world}"}.items()
        )]

    return LaunchDescription([
        start_paused_arg,
        set_gz_resource_path,
        set_gz_model_path,
        set_fastrtps_shm,
        OpaqueFunction(function=_gazebo_args),
    ])
