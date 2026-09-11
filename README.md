# pathfinder_bot
ROS 2 differential-drive robot with dual RGBD cameras and lidar, simulated in Gazebo for autonomous navigation.

## Overview

Pathfinder is a differential-drive robot built for simulation-based navigation work. It's equipped with front and rear RGBD cameras for all-around visual sensing and a 3D lidar for obstacle detection and mapping, making it suitable for tasks like SLAM, autonomous exploration, and obstacle avoidance.

This project builds on the ROS 2 / Gazebo robot description structure popularized by [Articulated Robotics](https://articulatedrobotics.xyz/) (see Credits below), extended with a dual-camera sensor setup and custom topic/bridge configuration.

## Features

- Differential drive base (diff-drive plugin via `gz-sim`)
- Front and rear RGBD cameras (`camera/front`, `camera/rear`)
- 3D lidar (gpu_lidar) for scanning and point cloud generation
- Full ROS 2 ↔ Gazebo topic bridging (odometry, TF, joint states, scan, camera streams)
- RViz configuration for visualizing the robot and sensor data
- Modular xacro-based robot description (links, joints, materials, inertials, Gazebo plugins)

## Prerequisites

- ROS 2 (tested on [Humble])
- Gazebo (Fortress)
- `ros_gz_sim`, `ros_gz_bridge`, `ros_gz_image`
- `xacro`
- `robot_state_publisher`

## Installation

```bash
cd ~/ros2_ws/src
git clone https://github.com/KanishkaHarwani/pathfinder_bot.git
cd ~/ros2_ws
colcon build --packages-select pathfinder_bot
source install/setup.bash
```

## Usage

### Launch the simulation

```bash
ros2 launch pathfinder_bot launch_sim.launch.py
```

This spawns the robot in Gazebo, starts `robot_state_publisher`, and brings up all ROS 2 ↔ Gazebo bridges (odometry, TF, lidar, cameras).

### Drive the robot manually

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

### Visualize in RViz

```bash
rviz2 -d src/pathfinder_bot/rviz/view_bot.rviz
```

## Package Structure
```pathfinder_bot/
├── description/ # URDF/xacro robot definition
├── launch/ # Launch files (sim + robot_state_publisher)
├── config/ # ROS 2 ↔ Gazebo bridge configuration
├── worlds/ # Gazebo world files
├── rviz/ # Saved RViz configuration
└── models/ # Custom Gazebo models/meshes (if any)
```

## Key Topics

| Topic | Description |
|---|---|
| `/cmd_vel` | Velocity commands (ROS → Gazebo) |
| `/odom` | Odometry (Gazebo → ROS) |
| `/tf` | Transform tree |
| `/scan` | Lidar scan |
| `/scan/points` | Lidar point cloud |
| `/joint_states` | Wheel joint states |
| `/camera/front/image` | Front camera RGB image |
| `/camera/front/depth_image` | Front camera depth image |
| `/camera/front/camera_info` | Front camera intrinsics |
| `/camera/rear/image` | Rear camera RGB image |
| `/camera/rear/depth_image` | Rear camera depth image |
| `/camera/rear/camera_info` | Rear camera intrinsics |

## Roadmap

- [ ] Custom simulation world
- [ ] SLAM / autonomous navigation integration
- [ ] Custom Path-Planning and Obstacle Avoidance test in gazebo

## Credits

Built on the ROS 2 / Gazebo robot description structure from [Articulated Robotics](https://articulatedrobotics.xyz/) by Josh Newans, extended with dual-camera sensing and custom bridge configuration.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
