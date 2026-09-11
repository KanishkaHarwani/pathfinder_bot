import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, AppendEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node


def generate_launch_description():

    # !!! MAKE SURE YOU SET THE PACKAGE NAME CORRECTLY !!!
    package_name = 'pathfinder_bot'  # <--- CHANGE ME

    # Include the robot_state_publisher launch file, provided by our own
    # package. Force sim time to be enabled.
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory(package_name), 'launch', 'rsp.launch.py'
        )]), launch_arguments={'use_sim_time': 'true'}.items()
    )

    # World file containing the Physics/UserCommands/SceneBroadcaster/Sensors
    # system plugins, ground plane, and sun. See worlds/empty.world.
    world = os.path.join(get_package_share_directory(package_name), 'worlds', 'empty.world')

    # Lets Gazebo find any meshes/models referenced by the package
    set_env_vars_resources = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        os.path.join(get_package_share_directory(package_name), 'models'))

    # Include the Gazebo launch file, provided by the ros_gz_sim package
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')]),
        launch_arguments={'gz_args': ['-r -v4 ', world]}.items()
    )

    # Run the spawner node from the ros_gz_sim package.
    # '-topic robot_description' spawns straight from the URDF that
    # robot_state_publisher is already publishing.
    spawn_entity = Node(
        package='ros_gz_sim', executable='create',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'pathfinder'
        ],
        output='screen'
    )

    # Bridge non-image topics (odom, tf, cmd_vel, joint_states, scan, camera_info, points)
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

    # Bridge the color and depth image topics with the more efficient
    # image-specific bridge
    ros_gz_image_bridge = Node(
        package='ros_gz_image',
        executable='image_bridge',
        arguments=[
            '/camera/image',
            '/camera/depth_image',
            '/camera2/image',
            '/camera2/depth_image',
        ]
    )

    # Launch them all!
    return LaunchDescription([
        rsp,
        set_env_vars_resources,
        gazebo,
        spawn_entity,
        ros_gz_image_bridge,
        ros_gz_bridge,
    ])
