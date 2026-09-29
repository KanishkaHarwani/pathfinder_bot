# pathfinder_bot
ROS 2 differential-drive robot with dual RGBD cameras and lidar, simulated in Gazebo for autonomous navigation.

## Overview

Pathfinder is a differential-drive robot built for simulation-based navigation work. It's equipped with front and rear RGBD cameras for all-around visual sensing and a 3D lidar for obstacle detection and mapping, making it suitable for tasks like SLAM, autonomous exploration, and obstacle avoidance.

This project builds on the ROS 2 / Gazebo robot description structure popularized by [Articulated Robotics](https://articulatedrobotics.xyz/) (see Credits below), extended with a dual-camera sensor setup, custom topic/bridge configuration, and full Nav2 autonomous navigation.

This README covers **v1**: everything running on a single machine. For a reference setup that splits simulation and navigation across two machines (a laptop and a Jetson), see [`distributed/README.md`](distributed/README.md).

## Features

- Differential drive base (diff-drive plugin via `gz-sim`)
- Front and rear RGBD cameras (`camera/front`, `camera/rear`)
- 3D lidar (gpu_lidar) for scanning and point cloud generation
- IMU mounted at `base_link` (coincident with the drive axis) for orientation, angular velocity, and linear acceleration
- Full ROS 2 ↔ Gazebo topic bridging (odometry, TF, joint states, scan, camera streams)
- SLAM mapping with `slam_toolbox`
- Autonomous navigation with Nav2 and AMCL — goal-pose navigation, localization, and obstacle avoidance for obstacles not present on the saved map, all tested working in simulation
- RViz configurations for both sensor visualization and navigation
- Modular xacro-based robot description (links, joints, materials, inertials, Gazebo plugins)

## Prerequisites

- Ubuntu 24.04
- ROS 2 Jazzy
- Gazebo Harmonic
- `ros_gz_sim`, `ros_gz_bridge`, `ros_gz_image` (`sudo apt install ros-jazzy-ros-gz`)
- `xacro`, `robot_state_publisher`, `rviz2`
- `joy`, `teleop_twist_joy`
- `nav2_bringup` (autonomous navigation), `slam_toolbox` (mapping)

## Installation

```bash
cd ~/ros2_ws/src
git clone https://github.com/KanishkaHarwani/pathfinder_bot.git
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select pathfinder_bot
source install/setup.bash
```

## Quick Start

Run everything (simulation, joystick input, teleop, Nav2, and RViz) with one command:

```bash
./startup.sh
```

This launches four terminal tabs:
1. Gazebo simulation (robot spawn + bridges)
2. `joy_node` (joystick driver, with a deadzone of ±0.2 to filter drift/noise)
3. `teleop_twist_joy` (converts joystick input to `/cmd_vel`)
4. Nav2 + RViz (`nav_bringup.launch.py`: map server, AMCL, planner, controller, and the navigation RViz layout)

The script auto-detects your workspace from its own location, so it works regardless of what you've named it — no editing required, as long as the repo is cloned into `src/` as usual.

## Usage

### Launch the simulation only

```bash
ros2 launch pathfinder_bot launch_sim.launch.py
```

This spawns the robot in Gazebo, starts `robot_state_publisher`, and brings up all ROS 2 ↔ Gazebo bridges (odometry, TF, lidar, cameras). It loads `worlds/warehouse_world.sdf`, a custom warehouse with outer walls, interior walls, blockers, and shelves.

### Check that everything works

With the simulation running, in a second terminal:

```bash
./check_sim.sh
```

This confirms that the clock, odometry, TF, joint states, IMU, lidar, and both cameras are publishing, then drives the robot forward briefly and checks that odometry changes.

### Drive the robot with a joystick

```bash
ros2 run joy joy_node --ros-args -p deadzone:=0.2
ros2 run teleop_twist_joy teleop_node --ros-args \
  -p axis_linear.x:=1 \
  -p axis_angular.yaw:=0 \
  -p scale_linear.x:=0.5 \
  -p scale_angular.yaw:=1.0 \
  -p enable_button:=0
```

The `deadzone:=0.2` parameter ignores joystick axis input between -0.2 and 0.2, preventing drift or noise from sending unintended movement commands.

### Navigate autonomously (Nav2)

With the simulation running:

```bash
ros2 launch pathfinder_bot nav_bringup.launch.py
```

This starts the map server (`maps/pathfinder_map.yaml`), AMCL, the Nav2 stack, and RViz (`rviz/pathfinder_nav.rviz`). The robot starts at the world origin, which AMCL is pre-configured to expect. In RViz, use **2D Goal Pose** to send the robot somewhere. If the robot's position on the map looks wrong, set it with **2D Pose Estimate**.

Useful arguments: `rviz:=false` (Nav2 only), `map:=<path>`, `params_file:=<path>`.

### Visualize sensors in RViz

To look at the camera streams and point clouds instead:

```bash
rviz2 -d src/pathfinder_bot/rviz/pathfinder.rviz
```
## Package Structure
```pathfinder_bot/
├── description/ # URDF/xacro robot definition
├── launch/ # Launch files (sim + robot_state_publisher)
├── config/ # ROS 2 ↔ Gazebo bridge and SLAM configuration
├── worlds/ # Gazebo world files
├── maps/ # Saved occupancy map (from slam_toolbox)
├── rviz/ # Saved RViz configuration
└── models/ # Custom Gazebo models/meshes (if any)
```

## Key Topics

| Topic | Description |
|---|---|
| `/clock` | Simulation time (Gazebo → ROS) |
| `/cmd_vel` | Velocity commands (ROS → Gazebo) |
| `/odom` | Odometry (Gazebo → ROS) |
| `/tf` | Transform tree |
| `/scan` | Lidar scan |
| `/scan/points` | Lidar point cloud |
| `/joint_states` | Wheel joint states |
| `/imu` | IMU orientation, angular velocity, linear acceleration |
| `/camera/front/image` | Front camera RGB image |
| `/camera/front/depth_image` | Front camera depth image |
| `/camera/front/camera_info` | Front camera intrinsics |
| `/camera/front/points` | Front camera point cloud |
| `/camera/rear/image` | Rear camera RGB image |
| `/camera/rear/depth_image` | Rear camera depth image |
| `/camera/rear/camera_info` | Rear camera intrinsics |
| `/camera/rear/points` | Rear camera point cloud |

## Roadmap

- [x] Custom simulation world
- [x] SLAM mapping (`slam_toolbox`, saved map in `maps/`)
- [x] Nav2 autonomous navigation with AMCL — localization, goal-pose navigation, and avoidance of obstacles not on the saved map, verified in simulation
- [ ] Distributed setup reference (simulation on a laptop, Nav2 on a Jetson) — see [`distributed/`](distributed/)
- [ ] Add a screenshot/GIF of the robot in Gazebo + RViz to this README

## Credits

Built on the ROS 2 / Gazebo robot description structure from [Articulated Robotics](https://articulatedrobotics.xyz/) by Josh Newans, extended with dual-camera sensing and custom bridge configuration.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
