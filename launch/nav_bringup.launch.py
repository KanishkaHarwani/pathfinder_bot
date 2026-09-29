import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


def generate_launch_description():
    """Nav2 (map_server, AMCL, planner, controller, ...) for Pathfinder.

    Replaces the old static map->odom transform: AMCL now publishes it.
    Runs with the simulation from launch_sim.launch.py (same machine, or on
    another machine sharing the ROS_DOMAIN_ID).
    """

    pkg = get_package_share_directory('pathfinder_bot')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    use_sim_time = LaunchConfiguration('use_sim_time')
    map_file = LaunchConfiguration('map')
    params_file = LaunchConfiguration('params_file')
    rviz = LaunchConfiguration('rviz')
    rviz_config = LaunchConfiguration('rviz_config')

    declare_args = [
        DeclareLaunchArgument(
            'use_sim_time', default_value='true',
            description='Use the Gazebo /clock'),
        DeclareLaunchArgument(
            'map', default_value=os.path.join(pkg, 'maps', 'pathfinder_map.yaml'),
            description='Full path to the map yaml file'),
        DeclareLaunchArgument(
            'params_file', default_value=os.path.join(pkg, 'config', 'nav2_params.yaml'),
            description='Full path to the Nav2 parameters file'),
        DeclareLaunchArgument(
            'rviz', default_value='true',
            description='Start RViz with the navigation layout'),
        DeclareLaunchArgument(
            'rviz_config', default_value=os.path.join(pkg, 'rviz', 'pathfinder_nav.rviz'),
            description='RViz config file'),
    ]

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')),
        launch_arguments={
            'map': map_file,
            'params_file': params_file,
            'use_sim_time': use_sim_time,
            'autostart': 'true',
        }.items(),
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(rviz),
        output='screen',
    )

    return LaunchDescription(declare_args + [nav2, rviz_node])
