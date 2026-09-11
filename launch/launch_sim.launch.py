import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, AppendEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node


def generate_launch_description():

    package_name = 'pathfinder_bot'

    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory(package_name), 'launch', 'rsp.launch.py'
        )]), launch_arguments={'use_sim_time': 'true'}.items()
    )

    world = os.path.join(get_package_share_directory(package_name), 'worlds', 'empty.world')

    set_env_vars_resources = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        os.path.join(get_package_share_directory(package_name), 'models'))

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')]),
        launch_arguments={'gz_args': ['-r -v4 ', world]}.items()
    )

    spawn_entity = Node(
        package='ros_gz_sim', executable='create',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'pathfinder'
        ],
        output='screen'
    )

    bridge_params = os.path.join(
        get_package_share_directory(package_name), 'config', 'gz_bridge.yaml')

    ros_gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '--ros-args',
            '-p', f'config_file:={bridge_params}',
        ],
        output='screen'
    )

    ros_gz_image_bridge = Node(
        package='ros_gz_image',
        executable='image_bridge',
        arguments=[
            '/camera/front/image',
            '/camera/front/depth_image',
            '/camera/rear/image',
            '/camera/rear/depth_image',
        ]
    )

    return LaunchDescription([
        rsp,
        set_env_vars_resources,
        gazebo,
        spawn_entity,
        ros_gz_image_bridge,
        ros_gz_bridge,
    ])
